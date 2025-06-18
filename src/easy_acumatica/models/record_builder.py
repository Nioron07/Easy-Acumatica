# easy_acumatica/models/record_builder.py
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, MutableMapping, Optional

Json = Dict[str, Any]


class _RecordBase:
    """
    Internal mix-in that equips concrete builders with fluent helpers
    and navigation (linked, detail, custom, up/root traversal).
    """

    # ------------------------------------------------------------------
    # System fields
    # ------------------------------------------------------------------
    def system(self, name: str, value: Any) -> "RecordBuilder":
        self._data[name] = value
        return self  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # General fields
    # ------------------------------------------------------------------
    def field(self, name: str, value: Any) -> "RecordBuilder":
        self._data[name] = {"value": value}
        return self  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Linked entities
    # ------------------------------------------------------------------
    def link(self, name: str) -> "RecordBuilder":
        child = self._data.setdefault(name, {})
        if not isinstance(child, MutableMapping):
            raise TypeError(f"{name!r} already exists and is not an object")
        return RecordBuilder(
            _existing=child,
            _parent=self,                 # link back to parent
            _root=self._root,             # keep original root
        )

    # ------------------------------------------------------------------
    # Detail entities
    # ------------------------------------------------------------------
    def add_detail(self, name: str) -> "RecordBuilder":
        arr = self._data.setdefault(name, [])
        if not isinstance(arr, list):
            raise TypeError(f"{name!r} already exists and is not a list")
        line: Json = {}
        arr.append(line)
        return RecordBuilder(
            _existing=line,
            _parent=self,
            _root=self._root,
        )

    # ------------------------------------------------------------------
    # Custom fields
    # ------------------------------------------------------------------
    def custom(
        self,
        view: str,
        field: str,
        *,
        value: Any,
        type_: str = "CustomStringField",
    ) -> "RecordBuilder":
        custom_block = self._data.setdefault("custom", {})
        view_block = custom_block.setdefault(view, {})
        view_block[field] = {"type": type_, "value": value}
        return self  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------
    def up(self) -> "RecordBuilder":
        """Return the parent builder (or self if already at top level)."""
        return self._parent or self  # type: ignore[attr-defined]

    def root(self) -> "RecordBuilder":
        """Return the very first (top-level) builder."""
        return self._root  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Final JSON
    # ------------------------------------------------------------------
    def build(self, deep: bool = True) -> Json:
        return deepcopy(self._data) if deep else self._data  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Dunders
    # ------------------------------------------------------------------
    def __getitem__(self, key: str) -> Any:               # noqa: D401
        return self._data[key]  # type: ignore[attr-defined]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value  # type: ignore[attr-defined]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._data!r})"


class RecordBuilder(_RecordBase):
    """
    Generic fluent builder for any Acumatica record.

    Features
    --------
    • `.field()`  – simple value fields
    • `.system()` – system/id fields
    • `.link()`   – nested (linked) entity
    • `.add_detail()` – lines/children
    • `.custom()` – custom & UDF
    • `.up()` / `.root()` – navigate back to parent or top
    • `.build()`  – final JSON dict ready for requests
    """

    @classmethod
    def for_contact(cls) -> "RecordBuilder":
        """Shortcut that pre-sets Type = Contact."""
        return cls().field("Type", "Contact")

    # ------------------------------------------------------------------
    def __init__(
        self,
        *,
        _existing: Optional[Json] = None,
        _parent: Optional["RecordBuilder"] = None,
        _root: Optional["RecordBuilder"] = None,
    ) -> None:
        self._data: Json = _existing if _existing is not None else {}
        self._parent = _parent
        self._root = _root or self
