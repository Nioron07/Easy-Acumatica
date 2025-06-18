"""easy_acumatica.models.contact
================================

Fluent builders for the *Contact* entity payloads used by
:pyclass:`easy_acumatica.contacts.ContactsService`.

Two public helpers
------------------
* :class:`Attribute`   – represents **one** element of the ``Attributes``
  array accepted by Acumatica.
* :class:`ContactBuilder` – chainable builder that assembles a valid JSON
  payload for *create-contact* requests.

The builder includes most common scalar fields exposed by the *Contact*
API so that you can describe a record without remembering the exact JSON
shape.  Each setter returns the same :class:`ContactBuilder` instance so
calls can be *chained*.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = ["Attribute", "ContactBuilder"]


# ---------------------------------------------------------------------------
# Attribute helper
# ---------------------------------------------------------------------------
class Attribute:  # pylint: disable=too-few-public-methods
    """Contact custom attribute wrapper."""

    def __init__(
        self,
        attribute_id: str,
        value: str,
        *,
        description: Optional[str] = None,
        value_description: Optional[str] = None,
        required: Optional[bool] = None,
        ref_note_id: Optional[str] = None,
    ) -> None:
        self.attribute_id = attribute_id
        self.value = value
        self.description = description
        self.value_description = value_description
        self.required = required
        self.ref_note_id = ref_note_id

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "AttributeID": {"value": self.attribute_id},
            "Value": {"value": self.value},
        }
        if self.description is not None:
            data["AttributeDescription"] = {"value": self.description}
        if self.value_description is not None:
            data["ValueDescription"] = {"value": self.value_description}
        if self.required is not None:
            data["Required"] = {"value": self.required}
        if self.ref_note_id is not None:
            data["RefNoteID"] = {"value": self.ref_note_id}
        return data


# ---------------------------------------------------------------------------
# ContactBuilder – fluent payload builder
# ---------------------------------------------------------------------------
class ContactBuilder:
    """Fluent builder for the *Contact* create/update payload.

    Examples
    --------
    >>> draft = (
    ...     ContactBuilder()
    ...     .first_name("Brian")
    ...     .last_name("Wooten")
    ...     .email("brian@example.com")
    ...     .phone1("+1 555‑1234", phone_type="Business 1")
    ...     .gender("Male")
    ...     .marital_status("Single")
    ...     .add_attribute("INTEREST", "Jam,Maint")
    ... )
    >>> payload = draft.build()  # ready for requests.put / post
    """

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}
        self._attrs: List[Attribute] = []

    # ------------------------------------------------------------------
    # internal helper
    def _set(self, field: str, value: Any) -> "ContactBuilder":
        self._data[field] = {"value": value}
        return self

    # ------------------------------------------------------------------
    # Core identity fields
    def first_name(self, name: str) -> "ContactBuilder":
        return self._set("FirstName", name)

    def last_name(self, name: str) -> "ContactBuilder":
        return self._set("LastName", name)

    def middle_name(self, name: str) -> "ContactBuilder":
        return self._set("MiddleName", name)

    # ------------------------------------------------------------------
    # Contact details
    def email(self, mail: str) -> "ContactBuilder":
        return self._set("Email", mail)

    def phone1(self, number: str, *, phone_type: str = "Business 1") -> "ContactBuilder":
        self._set("Phone1", number)
        return self._set("Phone1Type", phone_type)

    def phone2(self, number: str, *, phone_type: str = "Cell") -> "ContactBuilder":
        self._set("Phone2", number)
        return self._set("Phone2Type", phone_type)

    def phone3(self, number: str, *, phone_type: str = "Home") -> "ContactBuilder":
        self._set("Phone3", number)
        return self._set("Phone3Type", phone_type)

    def fax(self, number: str, *, fax_type: str = "Fax") -> "ContactBuilder":
        self._set("Fax", number)
        return self._set("FaxType", fax_type)

    def gender(self, value: str) -> "ContactBuilder":
        return self._set("Gender", value)

    def marital_status(self, value: str) -> "ContactBuilder":
        return self._set("MaritalStatus", value)

    def date_of_birth(self, iso_date: str) -> "ContactBuilder":
        """Date in ISO 8601 format ``YYYY-MM-DD``."""
        return self._set("DateOfBirth", iso_date)

    def job_title(self, title: str) -> "ContactBuilder":
        return self._set("JobTitle", title)

    def title(self, title: str) -> "ContactBuilder":
        return self._set("Title", title)

    def language_or_locale(self, locale: str) -> "ContactBuilder":
        return self._set("LanguageOrLocale", locale)

    def website(self, url: str) -> "ContactBuilder":
        return self._set("WebSite", url)

    def spouse_or_partner_name(self, name: str) -> "ContactBuilder":
        return self._set("SpouseOrPartnerName", name)

    # ------------------------------------------------------------------
    # Classification & ownership
    def contact_class(self, code: str) -> "ContactBuilder":
        return self._set("ContactClass", code)

    def contact_method(self, method: str) -> "ContactBuilder":
        return self._set("ContactMethod", method)

    def country_id(self, country: str) -> "ContactBuilder":
            """
            Sets Address.Country (required when *OverrideAccountAddress* = True).

            Examples
            --------
            >>> ContactBuilder().country_id("US")
            """
            addr = self._data.setdefault("Address", {})
            addr["Country"] = {"value": country}        # <-- nested!
            return self

    def override_account_address(self, flag: bool = True) -> "ContactBuilder":
        """
        Toggles the *Override Account Address* flag.  If you pass False the
        contact will inherit the address from its BusinessAccount, so the
        Address block becomes optional.
        """
        return self._set("OverrideAccountAddress", flag)

    def business_account(self, account: str) -> "ContactBuilder":
        return self._set("BusinessAccount", account)

    def company_name(self, name: str) -> "ContactBuilder":
        return self._set("CompanyName", name)

    def workgroup(self, grp: str) -> "ContactBuilder":
        return self._set("Workgroup", grp)

    def owner(self, owner: str) -> "ContactBuilder":
        return self._set("Owner", owner)

    def status(self, value: str) -> "ContactBuilder":
        """Contact status ("Active", "Inactive", etc.)."""
        return self._set("Status", value)

    def type(self, value: str) -> "ContactBuilder":
        """Contact type ("Contact", "Lead", …)."""
        return self._set("Type", value)

    # ------------------------------------------------------------------
    # Marketing / communication flags
    def do_not_call(self, flag: bool = True) -> "ContactBuilder":
        return self._set("DoNotCall", flag)

    def do_not_email(self, flag: bool = True) -> "ContactBuilder":
        return self._set("DoNotEmail", flag)

    def do_not_fax(self, flag: bool = True) -> "ContactBuilder":
        return self._set("DoNotFax", flag)

    def do_not_mail(self, flag: bool = True) -> "ContactBuilder":
        return self._set("DoNotMail", flag)

    def no_marketing(self, flag: bool = True) -> "ContactBuilder":
        return self._set("NoMarketing", flag)

    def no_mass_mail(self, flag: bool = True) -> "ContactBuilder":
        return self._set("NoMassMail", flag)

    # ------------------------------------------------------------------
    # Custom *Attributes* section
    def add_attribute(
        self,
        attribute_id: str,
        value: str,
        *,
        description: Optional[str] = None,
        value_description: Optional[str] = None,
        required: Optional[bool] = None,
        ref_note_id: Optional[str] = None,
    ) -> "ContactBuilder":
        # replace existing attribute with same ID
        self._attrs = [a for a in self._attrs if a.attribute_id != attribute_id]
        self._attrs.append(
            Attribute(
                attribute_id,
                value,
                description=description,
                value_description=value_description,
                required=required,
                ref_note_id=ref_note_id,
            )
        )
        return self

    # ------------------------------------------------------------------
    # Final JSON --------------------------------------------------------
    def build(self) -> Dict[str, Any]:  # noqa: D401 – simple verb
        if self._attrs:
            self._data["Attributes"] = [a.to_dict() for a in self._attrs]
        return self._data
