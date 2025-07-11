# src/easy_acumatica/models/tax_category_builder.py

from __future__ import annotations
from typing import Any, Dict
import copy


class TaxCategoryBuilder:
    """
    Fluent builder for the JSON payload to create a tax category.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}

    def set(self, field: str, value: Any) -> TaxCategoryBuilder:
        """Set a top-level field on the lead."""
        self._fields[field] = {"value": value}
        return self

    def active(self, isActive: bool) -> TaxCategoryBuilder:
        """Shortcut for .set('Active', active)."""
        return self.set("Active", isActive)

    def description(self, description: str) -> TaxCategoryBuilder:
        """Shortcut for .set('Description', description)."""
        return self.set("Description", description)

    def exclude_listed_taxes(self, excludeListedTaxes: bool) -> TaxCategoryBuilder:
        """Shortcut for .set('ExcludeListedTaxes', exclude_listed_taxes)."""
        return self.set("ExcludeListedTaxes", excludeListedTaxes)

    def tax_category_id(self, taxCategoryID: str) -> TaxCategoryBuilder:
        """Shortcut for .set('TaxCategoryID', id)."""
        return self.set("TaxCategoryID", taxCategoryID)

    def note(self, note: str) -> TaxCategoryBuilder:
        """Shortcut for .set('note', note)."""
        return self.set("note", note)

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        return copy.deepcopy(self._fields)

