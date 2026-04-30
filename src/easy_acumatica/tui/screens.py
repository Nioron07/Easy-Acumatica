"""Screens for the easy_acumatica TUI."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)


# --- Start screen ---------------------------------------------------------


class StartScreen(Screen):
    """Initial choice: .env, manual entry, or quit."""

    BINDINGS = [
        Binding('q', 'quit', 'Quit'),
        Binding('escape', 'quit', 'Quit', show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id='start-container'):
            yield Static('Easy Acumatica', id='start-title')
            yield Static('How do you want to connect?', id='start-subtitle')
            yield Button('Load from .env', id='use-env', variant='primary')
            yield Button('Enter credentials manually', id='use-manual')
            yield Button('Quit', id='quit')
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == 'use-env':
            self.app.push_screen(LoadingScreen(source='env'))
        elif button_id == 'use-manual':
            self.app.push_screen(CredentialsScreen())
        elif button_id == 'quit':
            self.app.exit()

    def action_quit(self) -> None:
        self.app.exit()


# --- Credentials screen ---------------------------------------------------


class CredentialsScreen(Screen):
    """Manual credential entry form."""

    BINDINGS = [
        Binding('escape', 'back', 'Back'),
    ]

    REQUIRED_FIELDS = ('base_url', 'username', 'password', 'tenant')

    def __init__(self, prefill: Optional[Dict[str, str]] = None) -> None:
        super().__init__()
        self._prefill = prefill or {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id='creds-container'):
            yield Static('Enter Acumatica Credentials', id='creds-title')

            yield Label('Base URL (required)')
            yield Input(
                value=self._prefill.get('base_url', ''),
                placeholder='https://your-instance.acumatica.com',
                id='f-base-url',
            )

            yield Label('Username (required)')
            yield Input(
                value=self._prefill.get('username', ''),
                id='f-username',
            )

            yield Label('Password (required)')
            yield Input(
                value=self._prefill.get('password', ''),
                password=True,
                id='f-password',
            )

            yield Label('Tenant (required)')
            yield Input(
                value=self._prefill.get('tenant', ''),
                id='f-tenant',
            )

            yield Label('Branch (optional)')
            yield Input(
                value=self._prefill.get('branch', ''),
                id='f-branch',
            )

            yield Label('Endpoint name')
            yield Input(
                value=self._prefill.get('endpoint_name', 'Default'),
                id='f-endpoint-name',
            )

            yield Static('', id='creds-error')

            with Horizontal(id='creds-buttons'):
                yield Button('Back', id='back')
                yield Button('Connect', id='connect', variant='primary')
        yield Footer()

    def _collect(self) -> Dict[str, str]:
        def val(widget_id: str) -> str:
            return self.query_one(f'#{widget_id}', Input).value.strip()

        return {
            'base_url': val('f-base-url'),
            'username': val('f-username'),
            'password': val('f-password'),
            'tenant': val('f-tenant'),
            'branch': val('f-branch'),
            'endpoint_name': val('f-endpoint-name') or 'Default',
        }

    def _validate(self, creds: Dict[str, str]) -> Optional[str]:
        missing = [k for k in self.REQUIRED_FIELDS if not creds.get(k)]
        if missing:
            return f"Missing required field(s): {', '.join(missing)}"
        if not creds['base_url'].startswith(('http://', 'https://')):
            return "base_url must start with http:// or https://"
        return None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'back':
            self.app.pop_screen()
        elif event.button.id == 'connect':
            creds = self._collect()
            err = self._validate(creds)
            if err:
                self.query_one('#creds-error', Static).update(err)
                return
            self.app.push_screen(LoadingScreen(source='manual', credentials=creds))

    def action_back(self) -> None:
        self.app.pop_screen()


# --- Loading screen -------------------------------------------------------


class LoadingScreen(Screen):
    """Shown while the client initializes on a worker thread."""

    def __init__(
        self,
        source: str,
        credentials: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__()
        self._source = source
        self._credentials = credentials or {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id='loading-container'):
            yield Static('Connecting...', id='loading-title')
            target = (self._credentials.get('base_url')
                      or 'Acumatica instance from .env')
            yield Static(
                f'Building client for {target}\n'
                f'(first run downloads the schema - up to ~10s)',
                id='loading-message',
            )
        yield Footer()

    def on_mount(self) -> None:
        # Kick off the worker that builds the client off the UI thread.
        self.app.start_client_init(self._source, self._credentials)


# --- Main screen ----------------------------------------------------------


class MainScreen(Screen):
    """Post-connection discovery screen: sidebar list + detail pane."""

    BINDINGS = [
        Binding('s', 'show_services', 'Services'),
        Binding('m', 'show_models', 'Models'),
        Binding('i', 'show_inquiries', 'Inquiries'),
        Binding('slash', 'focus_filter', 'Filter', show=True, key_display='/'),
        # `priority=True` so the screen's Enter handler wins over the
        # ListView's default Enter-to-activate behavior. That way clicking
        # a service only highlights it - invocation is always Enter.
        Binding('enter', 'invoke_selected', 'Call', show=True, priority=True),
        Binding('r', 'refresh', 'Refresh'),
        Binding('q', 'quit', 'Quit'),
    ]

    DEFAULT_MODE = 'services'

    def __init__(self) -> None:
        super().__init__()
        self._mode = self.DEFAULT_MODE
        self._all_items: List[str] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static('', id='conn-status')
        with Horizontal(id='main-body'):
            with Vertical(id='sidebar'):
                with Horizontal(id='sidebar-tabs'):
                    yield Button('Services', id='tab-services', classes='active')
                    yield Button('Models', id='tab-models')
                    yield Button('Inquiries', id='tab-inquiries')
                yield Input(placeholder='filter...', id='filter-input')
                yield ListView(id='list-view')
            with Vertical(id='detail-pane'):
                yield Static(
                    'Highlight an item on the left to see details.',
                    id='detail-content',
                    markup=True,
                )
        yield Footer()

    def on_mount(self) -> None:
        self._render_conn_status()
        self._load_items()

    def _render_conn_status(self) -> None:
        client = getattr(self.app, 'client', None)
        status = self.query_one('#conn-status', Static)
        if client is None:
            status.update('Not connected')
            return
        parts = [
            f'URL: {client.base_url}',
            f'Tenant: {client.tenant}',
            f'Endpoint: {client.endpoint_name}/{client.endpoint_version or "latest"}',
        ]
        status.update('  |  '.join(parts))

    def _load_items(self) -> None:
        client = getattr(self.app, 'client', None)
        if client is None:
            return
        if self._mode == 'services':
            self._all_items = list(client.list_services())
        elif self._mode == 'inquiries':
            self._all_items = list(client.list_inquiries())
        else:
            self._all_items = list(client.list_models())
        self._apply_filter('')

    def _apply_filter(self, needle: str) -> None:
        needle_lc = needle.strip().lower()
        view = self.query_one('#list-view', ListView)
        view.clear()
        for name in self._all_items:
            if not needle_lc or needle_lc in name.lower():
                view.append(ListItem(Label(name), name=name))
        # Reset detail pane when list changes
        self._render_detail(None)

    def _set_active_tab(self, mode: str) -> None:
        self._mode = mode
        self.query_one('#tab-services', Button).set_class(
            mode == 'services', 'active'
        )
        self.query_one('#tab-models', Button).set_class(
            mode == 'models', 'active'
        )
        self.query_one('#tab-inquiries', Button).set_class(
            mode == 'inquiries', 'active'
        )
        self.query_one('#filter-input', Input).value = ''
        self._load_items()
        # Footer needs to re-evaluate check_action() now that mode changed.
        self.refresh_bindings()

    def _render_detail(self, name: Optional[str]) -> None:
        content = self.query_one('#detail-content', Static)
        client = getattr(self.app, 'client', None)

        if name is None or client is None:
            content.update('Highlight an item on the left to see details.')
            return

        try:
            if self._mode == 'services':
                info = client.get_service_info(name)
                content.update(_render_service_info(info))
            elif self._mode == 'inquiries':
                info = client.get_inquiry_info(name)
                content.update(_render_inquiry_info(info))
            else:
                info = client.get_model_info(name)
                content.update(_render_model_info(info))
        except Exception as e:
            content.update(f'Error loading details: {e}')

    # -- Events -----------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'tab-services':
            self._set_active_tab('services')
        elif event.button.id == 'tab-models':
            self._set_active_tab('models')
        elif event.button.id == 'tab-inquiries':
            self._set_active_tab('inquiries')

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == 'filter-input':
            self._apply_filter(event.value)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        name = item.name if item is not None else None
        self._render_detail(name)

    # Note: no on_list_view_selected handler on purpose. ListView.Selected
    # fires on BOTH Enter and click, but we only want Enter to open the
    # call screen. The priority Enter binding above handles that case.

    def _open_call_screen(self, service_name: str) -> None:
        # Lazy import to keep the service_call module out of the hot path.
        from .service_call import ServiceCallScreen
        self.app.push_screen(ServiceCallScreen(service_name))

    def _open_inquiry_screen(self, method_name: str) -> None:
        from .service_call import ServiceCallScreen
        self.app.push_screen(
            ServiceCallScreen('Inquiries', inquiry_method=method_name)
        )

    def _open_model_builder(self, model_name: str) -> None:
        """Open the same nested ModelBuilderScreen used by put_entity, but
        for arbitrary model browsing. The builder shows a live code preview
        and a Copy button, so there's no post-save dialog - dismiss is a
        no-op once the user has copied what they need."""
        client = getattr(self.app, 'client', None)
        if client is None:
            return
        model_class = getattr(getattr(client, 'models', None), model_name, None)
        if model_class is None:
            self.app.push_screen(
                ErrorModal(f"Model '{model_name}' is not on client.models.")
            )
            return

        from .model_builder import ModelBuilderScreen

        self.app.push_screen(ModelBuilderScreen(model_class, top_level=True))

    def action_invoke_selected(self) -> None:
        view = self.query_one('#list-view', ListView)
        item = view.highlighted_child
        name = getattr(item, 'name', None) if item is not None else None
        if not name:
            return
        if self._mode == 'inquiries':
            self._open_inquiry_screen(name)
        elif self._mode == 'models':
            self._open_model_builder(name)
        else:
            self._open_call_screen(name)

    # -- Actions ----------------------------------------------------------

    def action_show_services(self) -> None:
        self._set_active_tab('services')

    def action_show_models(self) -> None:
        self._set_active_tab('models')

    def action_show_inquiries(self) -> None:
        self._set_active_tab('inquiries')

    def action_focus_filter(self) -> None:
        self.query_one('#filter-input', Input).focus()

    def action_refresh(self) -> None:
        client = getattr(self.app, 'client', None)
        if client is not None:
            client.refresh_schema()
        self._load_items()

    def action_quit(self) -> None:
        self.app.exit()


# --- Error modal ----------------------------------------------------------


class ErrorModal(ModalScreen[None]):
    """Simple dismissible error dialog."""

    BINDINGS = [Binding('escape', 'dismiss', 'Dismiss')]

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id='error-container'):
            yield Static('Error', id='error-title')
            yield Static(self._message, id='error-message')
            with Horizontal(id='error-buttons'):
                yield Button('Dismiss', id='dismiss', variant='primary')

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'dismiss':
            self.dismiss()

    def action_dismiss(self) -> None:
        self.dismiss()


# --- Formatters -----------------------------------------------------------


def _render_service_info(info: Dict[str, Any]) -> str:
    lines = [
        f"[b]{info.get('name', '?')}[/b]  (entity: {info.get('entity_name', '?')})",
        f"Client attribute: client.{info.get('client_attribute', '?')}",
        f"Endpoint: {info.get('endpoint_name', '?')}",
        f"Methods ({info.get('method_count', 0)}):",
        '',
    ]
    for m in info.get('methods', []):
        doc_lines = (m.get('docstring') or '').strip().splitlines()
        summary = doc_lines[0] if doc_lines else ''
        lines.append(f"  * {m['name']}" + (f" - {summary}" if summary else ''))
    return '\n'.join(lines)


def _render_inquiry_info(info: Dict[str, Any]) -> str:
    lines = [
        f"[b]{info.get('name', '?')}[/b]  (Generic Inquiry)",
        f"Call: client.inquiries.{info.get('method_name', info.get('name', '?'))}(options=...)",
    ]
    doc = (info.get('doc') or '').strip()
    if doc:
        lines.append('')
        lines.append(doc)
    return '\n'.join(lines)


def _render_model_info(info: Dict[str, Any]) -> str:
    lines = [
        f"[b]{info.get('name', '?')}[/b]  ({info.get('field_count', 0)} fields)",
    ]
    doc = (info.get('docstring') or '').strip()
    if doc:
        lines.append('')
        lines.append(doc)
    lines.extend(['', 'Fields:'])
    for fname, fmeta in info.get('fields', {}).items():
        required = '*' if fmeta.get('required') else ' '
        type_str = fmeta.get('type', '')
        lines.append(f"  {required} {fname}: {type_str}")
    return '\n'.join(lines)
