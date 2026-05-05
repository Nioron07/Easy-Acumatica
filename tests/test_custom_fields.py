"""Custom-field discovery + augmentation + payload routing tests.

Covers:
- ``walk_custom_fields`` correctly attaches discoveries to root and
  nested dataclass names by walking the OpenAPI annotations.
- ``augment_model_with_custom_fields`` rebuilds a dataclass with new
  typed fields plus ``__custom_field_meta__``.
- ``re_link_dataclass_annotations`` swaps stale child-class refs in
  parent ``__annotations__``.
- ``BaseDataClassModel.to_acumatica_payload`` routes augmented fields
  AND ad-hoc ``set_custom`` calls into ``payload["custom"]`` under the
  right view, with the correct ``{"type", "value"}`` envelope.
- End-to-end client integration: live mock server returns ``$adHocSchema``
  with a ``custom`` block; ``AcumaticaClient`` init applies discovery and
  the user can construct/serialize TestModel with the custom kwargs.
"""

from dataclasses import dataclass, fields
from typing import List, Optional

import pytest

from easy_acumatica import AcumaticaClient
from easy_acumatica.core import BaseDataClassModel
from easy_acumatica.model_factory import (
    apply_custom_field_discoveries,
    augment_model_with_custom_fields,
    re_link_dataclass_annotations,
    walk_custom_fields,
)


# ---------------------------------------------------------------------------
# walker
# ---------------------------------------------------------------------------


@dataclass
class _Address(BaseDataClassModel):
    City: Optional[str] = None


@dataclass
class _Detail(BaseDataClassModel):
    InventoryID: Optional[str] = None


@dataclass
class _Order(BaseDataClassModel):
    OrderType: Optional[str] = None
    BillToAddress: Optional[_Address] = None
    Details: Optional[List[_Detail]] = None


def _make_registry():
    return {"_Order": _Order, "_Address": _Address, "_Detail": _Detail}


def test_walker_finds_root_custom_fields():
    ad_hoc = {
        "OrderType": {},
        "custom": {
            "Document": {
                "AttributeColor": {"type": "CustomStringField", "value": None},
                "AttributeSize": {"type": "CustomStringField", "value": None},
            }
        },
    }
    found = walk_custom_fields(ad_hoc, _make_registry(), "_Order")
    assert ("_Order", "Document", "AttributeColor", "CustomStringField") in found
    assert ("_Order", "Document", "AttributeSize", "CustomStringField") in found


def test_walker_descends_into_nested_object():
    """A custom block on a nested object attaches to that nested model,
    not the parent."""
    ad_hoc = {
        "BillToAddress": {
            "City": {},
            "custom": {
                "Address": {"UsrAddrTag": {"type": "CustomStringField", "value": None}}
            },
        }
    }
    found = walk_custom_fields(ad_hoc, _make_registry(), "_Order")
    assert found == [("_Address", "Address", "UsrAddrTag", "CustomStringField")]


def test_walker_descends_into_list_elements():
    """Custom blocks on detail-array elements attach to the line model."""
    ad_hoc = {
        "Details": [
            {
                "InventoryID": {},
                "custom": {
                    "Transactions": {
                        "IsConfigurable": {"type": "CustomBooleanField", "value": None},
                        "SortOrder": {"type": "CustomIntField", "value": None},
                    }
                },
            }
        ]
    }
    found = walk_custom_fields(ad_hoc, _make_registry(), "_Order")
    assert ("_Detail", "Transactions", "IsConfigurable", "CustomBooleanField") in found
    assert ("_Detail", "Transactions", "SortOrder", "CustomIntField") in found


def test_walker_skips_empty_custom_blocks():
    ad_hoc = {"OrderType": {}, "custom": {}}
    assert walk_custom_fields(ad_hoc, _make_registry(), "_Order") == []


def test_walker_skips_unknown_nested_field_names():
    """Fields that aren't on the dataclass annotations are ignored - we
    don't try to navigate into them."""
    ad_hoc = {
        "MysteryNestedThing": {
            "custom": {"X": {"Y": {"type": "CustomStringField", "value": None}}}
        }
    }
    assert walk_custom_fields(ad_hoc, _make_registry(), "_Order") == []


# ---------------------------------------------------------------------------
# augmenter
# ---------------------------------------------------------------------------


def test_augment_adds_typed_fields():
    new_cls = augment_model_with_custom_fields(
        _Order,
        [
            ("Document", "AttributeColor", "CustomStringField"),
            ("Document", "UsrPriority", "CustomIntField"),
            ("Document", "UsrIsActive", "CustomBooleanField"),
        ],
    )
    field_names = {f.name for f in fields(new_cls)}
    assert {"AttributeColor", "UsrPriority", "UsrIsActive"} <= field_names

    instance = new_cls(
        OrderType="RM",
        AttributeColor="Red",
        UsrPriority=5,
        UsrIsActive=True,
    )
    assert instance.AttributeColor == "Red"
    assert instance.UsrPriority == 5
    assert instance.UsrIsActive is True


def test_augment_records_metadata():
    new_cls = augment_model_with_custom_fields(
        _Order,
        [("Document", "AttributeColor", "CustomStringField")],
    )
    assert new_cls.__custom_field_meta__["AttributeColor"] == (
        "Document",
        "CustomStringField",
    )


def test_augment_idempotent_on_empty_list():
    """No discoveries -> return the original class unchanged."""
    same = augment_model_with_custom_fields(_Order, [])
    assert same is _Order


def test_augment_skips_invalid_python_identifiers():
    """Acumatica returns related-field expansions like
    ``ResponseActivityNoteID!subject`` in custom blocks. These can't be
    dataclass field names - augmentation must skip them rather than
    crashing make_dataclass with TypeError."""
    new_cls = augment_model_with_custom_fields(
        _Order,
        [
            ("Document", "GoodField", "CustomStringField"),
            ("Document", "ResponseActivityNoteID!subject", "CustomStringField"),
            ("Document", "Field With Spaces", "CustomStringField"),
            ("Document", "1StartsWithDigit", "CustomStringField"),
        ],
    )
    field_names = {f.name for f in fields(new_cls)}
    assert "GoodField" in field_names
    assert "ResponseActivityNoteID!subject" not in field_names
    assert "Field With Spaces" not in field_names
    assert "1StartsWithDigit" not in field_names


def test_augment_does_not_shadow_existing_field():
    """If a custom-field name collides with an existing dataclass field,
    we keep the original field but still record the metadata so the
    field serializes to the custom block."""
    new_cls = augment_model_with_custom_fields(
        _Order,
        [("Document", "OrderType", "CustomStringField")],
    )
    field_names = [f.name for f in fields(new_cls)]
    assert field_names.count("OrderType") == 1
    assert new_cls.__custom_field_meta__["OrderType"] == (
        "Document",
        "CustomStringField",
    )


# ---------------------------------------------------------------------------
# re-link
# ---------------------------------------------------------------------------


def test_re_link_substitutes_nested_class_refs():
    registry = _make_registry()

    # Simulate augmenting _Detail (replacing class in registry) and check
    # that _Order.Details is re-linked to the new class.
    AugmentedDetail = augment_model_with_custom_fields(
        registry["_Detail"],
        [("Transactions", "UsrTag", "CustomStringField")],
    )
    registry["_Detail"] = AugmentedDetail

    # Pre re-link, _Order.__annotations__["Details"] still references the
    # OLD _Detail class (because ``@dataclass`` has cached it on the
    # class). re_link_dataclass_annotations fixes that.
    re_link_dataclass_annotations(registry)

    order_ann = registry["_Order"].__annotations__["Details"]
    # Walk Optional[List[X]] to confirm X is the augmented class.
    from typing import get_args, get_origin, Union

    args = get_args(order_ann)
    non_none = [a for a in args if a is not type(None)]
    assert len(non_none) == 1
    inner = get_args(non_none[0])[0]
    assert inner is AugmentedDetail


# ---------------------------------------------------------------------------
# payload routing
# ---------------------------------------------------------------------------


def test_payload_routes_discovered_custom_fields_under_custom_block():
    new_cls = augment_model_with_custom_fields(
        _Order,
        [
            ("Document", "AttributeColor", "CustomStringField"),
            ("Document", "UsrPriority", "CustomIntField"),
        ],
    )
    payload = new_cls(
        OrderType="RM",
        AttributeColor="Green",
        UsrPriority=3,
    ).to_acumatica_payload()

    assert payload["OrderType"] == {"value": "RM"}
    assert payload["custom"]["Document"]["AttributeColor"] == {
        "type": "CustomStringField",
        "value": "Green",
    }
    assert payload["custom"]["Document"]["UsrPriority"] == {
        "type": "CustomIntField",
        "value": 3,
    }


def test_payload_omits_unset_custom_fields():
    new_cls = augment_model_with_custom_fields(
        _Order,
        [("Document", "AttributeColor", "CustomStringField")],
    )
    payload = new_cls(OrderType="RM").to_acumatica_payload()
    assert "custom" not in payload  # no unset custom fields => no custom block


def test_set_custom_merges_into_custom_block():
    """set_custom() works on instances with no discovered metadata."""
    instance = _Order(OrderType="RM")
    instance.set_custom("Document", "UsrFoo", "bar")
    payload = instance.to_acumatica_payload()
    assert payload["custom"]["Document"]["UsrFoo"] == {
        "type": "CustomStringField",
        "value": "bar",
    }


def test_set_custom_infers_type_from_python_value():
    instance = _Order()
    instance.set_custom("Document", "UsrInt", 42)
    instance.set_custom("Document", "UsrFloat", 3.14)
    instance.set_custom("Document", "UsrBool", True)
    instance.set_custom("Document", "UsrStr", "x")
    payload = instance.to_acumatica_payload()
    types = {k: v["type"] for k, v in payload["custom"]["Document"].items()}
    assert types == {
        "UsrInt": "CustomIntField",
        "UsrFloat": "CustomDecimalField",
        "UsrBool": "CustomBooleanField",
        "UsrStr": "CustomStringField",
    }


def test_set_custom_explicit_type_overrides_inference():
    instance = _Order()
    instance.set_custom("Document", "UsrGuid", "abc-123", custom_type="CustomGuidField")
    payload = instance.to_acumatica_payload()
    assert payload["custom"]["Document"]["UsrGuid"]["type"] == "CustomGuidField"


def test_set_custom_and_discovered_field_coexist():
    new_cls = augment_model_with_custom_fields(
        _Order,
        [("Document", "AttributeColor", "CustomStringField")],
    )
    instance = new_cls(OrderType="RM", AttributeColor="Red")
    instance.set_custom("Document", "UsrAdHoc", "X")
    payload = instance.to_acumatica_payload()
    document = payload["custom"]["Document"]
    assert document["AttributeColor"] == {"type": "CustomStringField", "value": "Red"}
    assert document["UsrAdHoc"] == {"type": "CustomStringField", "value": "X"}


# ---------------------------------------------------------------------------
# end-to-end with the mock server
# ---------------------------------------------------------------------------


def test_client_init_discovers_and_augments_test_model(base_client_config, reset_server_state):
    """Mock $adHocSchema returns three custom fields under Document. After
    init, TestModel should accept them as kwargs and serialize correctly."""
    client = AcumaticaClient(**base_client_config)

    TestModel = client.models.TestModel
    field_names = {f.name for f in fields(TestModel)}
    assert {"AttributeColor", "AttributeSize", "UsrPriority"} <= field_names

    meta = TestModel.__custom_field_meta__
    assert meta["AttributeColor"] == ("Document", "CustomStringField")
    assert meta["UsrPriority"] == ("Document", "CustomIntField")

    payload = TestModel(
        Name="X",
        AttributeColor="Blue",
        AttributeSize="Large",
        UsrPriority=9,
    ).to_acumatica_payload()
    assert payload["custom"]["Document"] == {
        "AttributeColor": {"type": "CustomStringField", "value": "Blue"},
        "AttributeSize": {"type": "CustomStringField", "value": "Large"},
        "UsrPriority": {"type": "CustomIntField", "value": 9},
    }


def test_ad_hoc_schemas_cached_to_disk(base_client_config, reset_server_state, tmp_path):
    """First connect fetches $adHocSchema for every entity; second
    connect (with the same cache directory and unchanged OpenAPI hash)
    must reuse the cached responses and skip the per-entity HTTP fetch."""
    import pickle
    from unittest.mock import patch

    cfg = dict(base_client_config)
    cfg.update(cache_methods=True, cache_dir=tmp_path, force_rebuild=True)

    client_a = AcumaticaClient(**cfg)
    cached_tags = set(client_a._ad_hoc_schemas.keys())
    assert cached_tags, "discovery should have populated _ad_hoc_schemas"
    client_a.close()

    cache_files = list(tmp_path.glob("*.pkl"))
    assert len(cache_files) == 1
    with open(cache_files[0], "rb") as f:
        cache_data = pickle.load(f)
    assert cache_data["version"] == "1.2"
    assert set(cache_data["ad_hoc_schemas"]) == cached_tags

    # Second connect - same cache dir, no force_rebuild. The fetch
    # helper should not be called even once because the cached schemas
    # are reused.
    cfg2 = dict(base_client_config)
    cfg2.update(cache_methods=True, cache_dir=tmp_path, force_rebuild=False)
    with patch.object(
        AcumaticaClient,
        "_fetch_one_ad_hoc_schema",
        autospec=True,
    ) as mocked_fetch:
        client_b = AcumaticaClient(**cfg2)
    assert mocked_fetch.call_count == 0, (
        "second connect should reuse cached $adHocSchema, not refetch"
    )
    # Augmentation still happened from the cached schemas.
    field_names = {f.name for f in fields(client_b.models.TestModel)}
    assert {"AttributeColor", "AttributeSize", "UsrPriority"} <= field_names
    client_b.close()


def test_stub_generation_includes_augmented_fields(base_client_config, reset_server_state):
    """generate_model_stub iterates dataclass_fields, so an augmented
    model produces a .pyi block that includes the custom fields with the
    proper Python types - no separate generate_stubs path needed."""
    from easy_acumatica.generate_stubs import generate_model_stub

    client = AcumaticaClient(**base_client_config)
    rendered = "\n".join(generate_model_stub(client.models.TestModel))
    assert "AttributeColor: str | None = ..." in rendered
    assert "AttributeSize: str | None = ..." in rendered
    assert "UsrPriority: int | None = ..." in rendered
