# tests/test_contact_builder.py
"""
Unit tests for easy_acumatica.models.contact_builder
"""

from easy_acumatica.models.contact_builder import Attribute, ContactBuilder


# ---------------------------------------------------------------------------
# Attribute helper
# ---------------------------------------------------------------------------
def test_attribute_minimal():
    attr = Attribute("INTEREST", "Jam,Maint")
    dct = attr.to_dict()
    assert dct == {
        "AttributeID": {"value": "INTEREST"},
        "Value": {"value": "Jam,Maint"},
    }


def test_attribute_full():
    attr = Attribute(
        "SIZE",
        "XL",
        description="T-Shirt Size",
        value_description="Extra Large",
        required=True,
        ref_note_id="guid-123",
    )
    dct = attr.to_dict()
    assert dct["AttributeDescription"]["value"] == "T-Shirt Size"
    assert dct["Required"]["value"] is True
    assert dct["RefNoteID"]["value"] == "guid-123"


# ---------------------------------------------------------------------------
# ContactBuilder
# ---------------------------------------------------------------------------
def test_builder_minimal_fields():
    draft = (
        ContactBuilder()
        .first_name("John")
        .last_name("Doe")
        .email("john@example.com")
    )
    payload = draft.build()
    assert payload["FirstName"]["value"] == "John"
    assert payload["Email"]["value"] == "john@example.com"


def test_builder_chain_returns_same_instance():
    builder = ContactBuilder()
    first = builder.first_name("A")
    second = first.last_name("B")
    assert first is builder and second is builder


def test_builder_attributes_added():
    builder = (
        ContactBuilder()
        .add_attribute("INTEREST", "Jam")
        .add_attribute("INTEREST", "Jam,Maint")  # overwrite same id
        .add_attribute("VIP", "1", required=True)
    )
    payload = builder.build()
    attrs = {a["AttributeID"]["value"]: a for a in payload["Attributes"]}

    # overwrite succeeded
    assert attrs["INTEREST"]["Value"]["value"] == "Jam,Maint"
    # second attribute exists
    assert attrs["VIP"]["Required"]["value"] is True


def test_builder_all_fields_snapshot():
    """Quick sanity check that .build() returns a dict, not an empty one."""
    builder = (
        ContactBuilder()
        .first_name("Jane")
        .last_name("Roe")
        .gender("Female")
        .marital_status("Single")
        .status("Active")
        .phone1("555-0100")
        .add_attribute("SOURCE", "Web")
    )
    payload = builder.build()
    # Make sure a handful of fields landed where expected
    assert payload["Gender"]["value"] == "Female"
    assert payload["Status"]["value"] == "Active"
    assert "Attributes" in payload and len(payload["Attributes"]) == 1
