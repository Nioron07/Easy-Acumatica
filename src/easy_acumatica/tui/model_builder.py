"""Recursive model builder screen for the TUI debug menu.

Used by `ServiceCallScreen` for the put_entity flow. The user picks a
service whose entity model has primitive, nested, and list-of-model
fields, and this screen lets them fill values one field at a time.
Nested models push a child instance of this screen, so the structure
is naturally recursive.

Returns a constructed `BaseDataClassModel` instance via `dismiss(model)`,
or `None` on Cancel.
"""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, get_type_hints

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label, Static

from ..core import BaseDataClassModel
from .code_render import classify_field, render_model


# --- Primitive coercion helpers ------------------------------------------


def _coerce_primitive(raw: str, target_type: Any) -> Any:
    """Convert a text input value to the target Python type.

    Returns ``None`` for empty input. Raises ValueError on bad input so
    the caller can surface a clean error.
    """
    raw = (raw or "").strip()
    if raw == "":
        return None
    if target_type is bool:
        lowered = raw.lower()
        if lowered in ('true', '1', 'yes', 'y', 'on'):
            return True
        if lowered in ('false', '0', 'no', 'n', 'off'):
            return False
        raise ValueError(f"expected bool (true/false), got {raw!r}")
    if target_type is int:
        return int(raw)
    if target_type is float:
        return float(raw)
    if target_type is datetime:
        # ISO 8601: "2025-04-27T10:30:00" or "2025-04-27"
        return datetime.fromisoformat(raw)
    # str / Any / unknown - pass through as a string
    return raw


def _split_csv(raw: str, item_type: Any) -> Optional[List[Any]]:
    """Comma-split + per-item primitive coercion. Empty -> None."""
    raw = (raw or "").strip()
    if raw == "":
        return None
    return [_coerce_primitive(p, item_type) for p in raw.split(',')]


# --- Screen --------------------------------------------------------------


class ModelBuilderScreen(ModalScreen[Optional[BaseDataClassModel]]):
    """
    Form screen for constructing a `BaseDataClassModel` instance.

    Returns the built instance via ``dismiss(model)``, or ``None`` on
    cancel. Nested model fields are filled by pushing a child
    `ModelBuilderScreen` and capturing the dismiss result.
    """

    BINDINGS = [
        Binding('escape', 'cancel', 'Back'),
        Binding('ctrl+s', 'save', 'Save', show=True, key_display='Ctrl+S'),
        Binding('ctrl+y', 'copy_preview', 'Copy code', show=True, key_display='Ctrl+Y'),
    ]

    def __init__(
        self,
        model_class: Type[BaseDataClassModel],
        prefill: Optional[Dict[str, Any]] = None,
        *,
        top_level: bool = False,
    ) -> None:
        super().__init__()
        self._model_class = model_class
        # Field name -> already-built nested model or list (for non-primitive
        # fields). Primitives are read straight from their Input widgets.
        self._values: Dict[str, Any] = dict(prefill or {})
        self._field_kinds: Dict[str, Dict[str, Any]] = {}
        self._row_count_per_list: Dict[str, int] = {}
        # Cached last-rendered preview text - used by the Copy action so it
        # doesn't have to rebuild the snippet from form state.
        self._last_preview: str = ''
        # Field-name filter substring (case-insensitive). Empty string =
        # show every field. Augmented dataclasses can have hundreds of
        # custom fields; the filter narrows the form to a manageable
        # subset without losing already-entered values.
        self._field_filter: str = ''
        # Top-level mode (opened directly from the Models tab) shows just
        # Copy + Back - there is no parent to feed a saved instance back
        # into, so the live preview is the only output. Nested builders
        # opened by put_entity / nested fields still get Save + Cancel.
        self._top_level = top_level

    # -- Compose ---------------------------------------------------------

    def compose(self) -> ComposeResult:
        with Container(id='builder-root'):
            yield Static(
                f'Build [b]{self._model_class.__name__}[/b]',
                id='builder-title',
                markup=True,
            )
            help_text = (
                'Leave a field blank to omit it. Esc closes, Ctrl+Y copies code.'
                if self._top_level
                else 'Leave a field blank to omit it. Esc cancels, Ctrl+S saves, Ctrl+Y copies code.'
            )
            yield Static(help_text, id='builder-help', markup=False)
            with Horizontal(id='builder-body'):
                with Vertical(id='builder-fields-wrap'):
                    # Field-name filter. Augmented models can have many
                    # custom fields; this narrows the form to fields
                    # whose name contains the substring (case-insensitive).
                    yield Input(
                        placeholder='filter fields...',
                        id='builder-filter',
                    )
                    # The fields are inside a VerticalScroll so a tall
                    # model scrolls within the panel while the title +
                    # buttons stay anchored to the panel edges.
                    yield VerticalScroll(id='builder-fields')
                with Vertical(id='builder-preview-wrap'):
                    yield Static('Equivalent Python', id='builder-preview-title')
                    # Wrap the preview in a VerticalScroll so long
                    # snippets can scroll inside the panel rather than
                    # bleeding past the modal's bottom edge.
                    with VerticalScroll(id='builder-preview-scroll'):
                        yield Static('', id='builder-preview', markup=False)
            with Horizontal(id='builder-buttons'):
                if self._top_level:
                    yield Button('Back', id='cancel')
                    yield Button('Copy code', id='copy-preview', variant='primary')
                else:
                    yield Button('Cancel', id='cancel')
                    yield Button('Copy code', id='copy-preview')
                    yield Button('Save', id='save', variant='primary')
            yield Static('', id='builder-status', markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.call_after_refresh(self._populate_fields)
        self.call_after_refresh(self._render_preview)

    # -- Field population ------------------------------------------------

    def _resolve_hints(self) -> Dict[str, Any]:
        """Resolve forward references against the runtime models module."""
        try:
            from .. import models as models_module
            namespace = dict(models_module.__dict__)
        except Exception:
            namespace = {}
        try:
            return get_type_hints(self._model_class, globalns=namespace, localns=namespace)
        except Exception:
            # Fallback to raw __annotations__ on the class
            return dict(getattr(self._model_class, '__annotations__', {}))

    async def _populate_fields(self) -> None:
        container = self.query_one('#builder-fields', VerticalScroll)
        await container.remove_children()

        if not is_dataclass(self._model_class):
            await container.mount(Static(
                f'{self._model_class.__name__} is not a dataclass.',
            ))
            return

        hints = self._resolve_hints()

        needle = self._field_filter.strip().lower()
        for f in fields(self._model_class):
            if f.name.startswith('_'):
                continue
            ann = hints.get(f.name, Any)
            kind = classify_field(ann)
            # Track the kind for every field so collect/snapshot/preview
            # work correctly even when a field is filtered out of view.
            self._field_kinds[f.name] = kind
            if needle and needle not in f.name.lower():
                continue
            await self._mount_field_row(container, f.name, kind)

    async def _mount_field_row(
        self,
        container: Container,
        field_name: str,
        kind: Dict[str, Any],
    ) -> None:
        """Render the input(s) for one field."""
        kind_name = kind['kind']

        if kind_name == 'primitive':
            type_label = self._type_label(kind.get('type'))
            await container.mount(Label(f'{field_name}  ({type_label})'))
            current = self._values.get(field_name)
            await container.mount(Input(
                value='' if current is None else str(current),
                placeholder=f'{type_label} value',
                id=f'p-{field_name}',
            ))
            return

        if kind_name == 'list-primitive':
            type_label = self._type_label(kind.get('item'))
            await container.mount(Label(
                f'{field_name}  (List[{type_label}], comma-separated)'
            ))
            current = self._values.get(field_name)
            value_str = ', '.join(str(x) for x in current) if current else ''
            await container.mount(Input(
                value=value_str,
                placeholder='value1, value2, ...',
                id=f'p-{field_name}',
            ))
            return

        if kind_name == 'model':
            child_class = kind['model']
            await container.mount(Label(
                f'{field_name}  (nested {child_class.__name__})'
            ))
            with_value = self._values.get(field_name)
            status = (
                f'[green][configured: {child_class.__name__}][/green]'
                if with_value is not None
                else '[dim][not set][/dim]'
            )
            await container.mount(Horizontal(
                Button(
                    f'Build {child_class.__name__}',
                    id=f'build-{field_name}',
                ),
                Static(status, id=f'status-{field_name}', markup=True),
                classes='nested-row',
            ))
            return

        if kind_name == 'list-model':
            child_class = kind['model']
            await container.mount(Label(
                f'{field_name}  (List[{child_class.__name__}])'
            ))
            existing = self._values.get(field_name) or []
            self._values[field_name] = list(existing)  # ensure mutability
            for i, _row in enumerate(existing):
                await self._mount_list_row(container, field_name, child_class, i)
            await container.mount(Button(
                f'+ Add {child_class.__name__}',
                id=f'addrow-{field_name}',
            ))
            return

        # Unknown kind - render as a permissive primitive
        await container.mount(Label(f'{field_name}  (Any)'))
        await container.mount(Input(id=f'p-{field_name}'))

    async def _mount_list_row(
        self,
        container: Container,
        field_name: str,
        child_class: Type[BaseDataClassModel],
        index: int,
    ) -> None:
        await container.mount(Horizontal(
            Static(
                f'  [{index}] {child_class.__name__}',
                id=f'rowinfo-{field_name}-{index}',
            ),
            Button('Edit', id=f'editrow-{field_name}-{index}'),
            Button('Remove', id=f'removerow-{field_name}-{index}'),
            classes='list-row',
        ))

    @staticmethod
    def _type_label(t: Any) -> str:
        if t is None or t is Any:
            return 'Any'
        if hasattr(t, '__name__'):
            return t.__name__
        return str(t)

    # -- Events ----------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ''
        if bid == 'cancel':
            self.action_cancel()
        elif bid == 'save':
            self.action_save()
        elif bid == 'copy-preview':
            self.action_copy_preview()
        elif bid.startswith('build-'):
            field_name = bid.removeprefix('build-')
            self._open_nested_builder(field_name)
        elif bid.startswith('addrow-'):
            field_name = bid.removeprefix('addrow-')
            self._append_list_row(field_name)
        elif bid.startswith('editrow-'):
            rest = bid.removeprefix('editrow-')
            field_name, _, idx = rest.rpartition('-')
            self._edit_list_row(field_name, int(idx))
        elif bid.startswith('removerow-'):
            rest = bid.removeprefix('removerow-')
            field_name, _, idx = rest.rpartition('-')
            self._remove_list_row(field_name, int(idx))

    def on_input_changed(self, event: Input.Changed) -> None:
        """Re-render the live code preview as the user edits inputs.

        The field-name filter is handled separately: snapshot the
        currently-visible primitive inputs into ``self._values`` so they
        survive the form rebuild, update the filter, then re-populate
        with only matching fields shown.
        """
        if event.input.id == 'builder-filter':
            self._snapshot_primitive_inputs()
            self._field_filter = event.value
            self.call_after_refresh(self._populate_fields)
            self.call_after_refresh(self._render_preview)
            return
        self._render_preview()

    # -- Nested model handling ------------------------------------------

    def _open_nested_builder(self, field_name: str) -> None:
        kind = self._field_kinds.get(field_name)
        if not kind or kind['kind'] != 'model':
            return
        child_class = kind['model']

        def _on_done(result: Optional[BaseDataClassModel]) -> None:
            if result is None:
                return
            self._values[field_name] = result
            try:
                self.query_one(f'#status-{field_name}', Static).update(
                    f'[green][configured: {child_class.__name__}][/green]'
                )
            except Exception:
                pass
            self._render_preview()

        self.app.push_screen(ModelBuilderScreen(child_class), _on_done)

    def _append_list_row(self, field_name: str) -> None:
        kind = self._field_kinds.get(field_name)
        if not kind or kind['kind'] != 'list-model':
            return
        child_class = kind['model']

        def _on_done(result: Optional[BaseDataClassModel]) -> None:
            if result is None:
                return
            self._values.setdefault(field_name, []).append(result)
            # Preserve in-flight primitive input text before _populate_fields
            # re-mounts the form (it reads initial values from self._values).
            self._snapshot_primitive_inputs()
            self.call_after_refresh(self._populate_fields)
            self.call_after_refresh(self._render_preview)

        self.app.push_screen(ModelBuilderScreen(child_class), _on_done)

    def _edit_list_row(self, field_name: str, index: int) -> None:
        kind = self._field_kinds.get(field_name)
        rows = self._values.get(field_name) or []
        if not kind or kind['kind'] != 'list-model' or index >= len(rows):
            return
        child_class = kind['model']

        def _on_done(result: Optional[BaseDataClassModel]) -> None:
            if result is None:
                return
            rows[index] = result
            self._render_preview()

        self.app.push_screen(ModelBuilderScreen(child_class), _on_done)

    def _remove_list_row(self, field_name: str, index: int) -> None:
        rows = self._values.get(field_name) or []
        if 0 <= index < len(rows):
            del rows[index]
            self._snapshot_primitive_inputs()
            self.call_after_refresh(self._populate_fields)
            self.call_after_refresh(self._render_preview)

    def _snapshot_primitive_inputs(self) -> None:
        """Capture every primitive / list-primitive Input's current value
        into ``self._values``.

        ``_populate_fields`` re-creates Inputs from ``self._values``, so we
        need to push the user's in-flight text back before rebuilding the
        form. Without this, "+ Add" or "Remove" on a list field wipes the
        primitive Inputs the user has already filled in.
        """
        for field_name, kind in self._field_kinds.items():
            kind_name = kind.get('kind')
            if kind_name not in ('primitive', 'list-primitive'):
                continue
            try:
                widget = self.query_one(f'#p-{field_name}', Input)
            except Exception:
                continue
            raw = widget.value
            if kind_name == 'primitive':
                try:
                    coerced = _coerce_primitive(raw, kind.get('type'))
                except ValueError:
                    coerced = raw  # keep raw text so it survives re-mount
                if coerced is None:
                    self._values.pop(field_name, None)
                else:
                    self._values[field_name] = coerced
            else:  # list-primitive
                try:
                    coerced = _split_csv(raw, kind.get('item'))
                except ValueError:
                    coerced = [p.strip() for p in raw.split(',') if p.strip()]
                if not coerced:
                    self._values.pop(field_name, None)
                else:
                    self._values[field_name] = coerced

    # -- Save / cancel --------------------------------------------------

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_save(self) -> None:
        if self._top_level:
            return  # no parent to receive a saved instance
        try:
            instance = self._build_instance()
        except ValueError as e:
            self.query_one('#builder-status', Static).update(
                f'[red]Invalid input: {e}[/red]'
            )
            return
        self.dismiss(instance)

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        """Hide the Save footer hint in top-level mode - it has no effect."""
        if action == 'save' and self._top_level:
            return None
        return True

    def _build_instance(self, *, lenient: bool = False) -> BaseDataClassModel:
        """Build a model instance from the current form state.

        When ``lenient`` is True, primitive coercion errors are skipped
        rather than raised - used by the live preview so partial / invalid
        input doesn't blank the snippet.
        """
        kwargs: Dict[str, Any] = {}
        for field_name, kind in self._field_kinds.items():
            kind_name = kind['kind']
            if kind_name == 'primitive':
                # Fall back to the snapshot in ``self._values`` when the
                # widget isn't mounted - happens when the user filtered
                # the field out of view after entering a value.
                try:
                    widget_value = self.query_one(f'#p-{field_name}', Input).value
                except Exception:
                    snapshot = self._values.get(field_name)
                    if snapshot is not None:
                        kwargs[field_name] = snapshot
                    continue
                try:
                    value = _coerce_primitive(widget_value, kind.get('type'))
                except ValueError:
                    if lenient:
                        continue
                    raise
                if value is not None:
                    kwargs[field_name] = value
            elif kind_name == 'list-primitive':
                try:
                    widget_value = self.query_one(f'#p-{field_name}', Input).value
                except Exception:
                    snapshot = self._values.get(field_name)
                    if snapshot:
                        kwargs[field_name] = list(snapshot)
                    continue
                try:
                    value = _split_csv(widget_value, kind.get('item'))
                except ValueError:
                    if lenient:
                        continue
                    raise
                if value is not None:
                    kwargs[field_name] = value
            elif kind_name == 'model':
                v = self._values.get(field_name)
                if v is not None:
                    kwargs[field_name] = v
            elif kind_name == 'list-model':
                v = self._values.get(field_name)
                if v:  # non-empty list
                    kwargs[field_name] = list(v)
        return self._model_class(**kwargs)

    # -- Live preview ----------------------------------------------------

    def _render_preview(self) -> None:
        """Re-render the equivalent-Python snippet from current form state.

        Designed to be cheap and silent on partial / invalid input - this
        runs on every Input change and after every nested-builder dismiss.
        """
        try:
            snippet = self._build_preview()
        except Exception:
            snippet = ''
        self._last_preview = snippet
        try:
            self.query_one('#builder-preview', Static).update(snippet)
        except Exception:
            pass

    def _build_preview(self) -> str:
        try:
            instance = self._build_instance(lenient=True)
        except Exception:
            return ''
        lines, imports, top_var = render_model(instance)
        out: List[str] = []
        if imports:
            out.append(
                'from easy_acumatica.models import '
                + ', '.join(sorted(imports))
            )
            out.append('')
        out.extend(lines)
        if top_var and (not lines or top_var not in lines[-1]):
            out.append(top_var)
        return '\n'.join(out)

    def action_copy_preview(self) -> None:
        if not self._last_preview:
            return
        try:
            self.app.copy_to_clipboard(self._last_preview)
            self.query_one('#builder-status', Static).update(
                '[green]Copied to clipboard.[/green]'
            )
        except Exception as e:
            self.query_one('#builder-status', Static).update(
                f'[red]Copy failed: {e}[/red]'
            )
