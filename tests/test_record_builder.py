# tests/test_record_builder.py

from easy_acumatica.models.record_builder import RecordBuilder


# ---------------------------------------------------------------------
# Basic fields and build()
# ---------------------------------------------------------------------
def test_field_and_system_build():
    rb = (
        RecordBuilder()
        .field("CustomerID", "JOHNGOOD")
        .system("rowNumber", 1)
    )
    result = rb.build(deep=False)       # no copy → inspect internals

    assert result["CustomerID"]["value"] == "JOHNGOOD"
    assert result["rowNumber"] == 1


# ---------------------------------------------------------------------
# Linked entities + navigation helpers
# ---------------------------------------------------------------------
def test_link_up_root_navigation():
    root = RecordBuilder().field("CustomerID", "JOHNGOOD")

    contact = root.link("MainContact")          # into linked entity
    assert contact is not root                  # different object
    assert contact.up() is root                 # up() works
    assert contact.root() is root               # root() from child

    # modify nested then pop back up
    contact.field("Email", "demo@gmail.com").up().field("CustomerClass", "DEFAULT")

    payload = root.build()
    assert payload["MainContact"]["Email"]["value"] == "demo@gmail.com"
    assert payload["CustomerClass"]["value"] == "DEFAULT"


# ---------------------------------------------------------------------
# Detail entities
# ---------------------------------------------------------------------
def test_add_detail_lines():
    so = RecordBuilder()
    so.add_detail("Details").field("InventoryID", "AALEGO500").field("Quantity", 10)
    so.add_detail("Details").field("InventoryID", "CONGRILL").field("Quantity", 1)

    body = so.build()
    assert isinstance(body["Details"], list)
    assert body["Details"][0]["InventoryID"]["value"] == "AALEGO500"
    assert body["Details"][1]["Quantity"]["value"] == 1


# ---------------------------------------------------------------------
# Custom fields
# ---------------------------------------------------------------------
def test_custom_field_block():
    rb = (
        RecordBuilder()
        .custom("DefContact", "UsrPersonalID", value="AB123456", type_="CustomStringField")
    )
    data = rb.build()
    assert data["custom"]["DefContact"]["UsrPersonalID"] == {
        "type": "CustomStringField",
        "value": "AB123456",
    }


# ---------------------------------------------------------------------
# Chaining returns same-type builders (sanity for mypy / fluency)
# ---------------------------------------------------------------------
def test_chaining_returns_builder_instances():
    rb = RecordBuilder()
    assert isinstance(rb.field("Foo", "Bar"), RecordBuilder)
    assert isinstance(rb.link("Nested"), RecordBuilder)
    assert isinstance(rb.add_detail("Lines"), RecordBuilder)
    assert isinstance(rb.custom("V", "F", value=1), RecordBuilder)
