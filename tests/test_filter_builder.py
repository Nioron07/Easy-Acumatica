# tests/test_filters.py
"""
Unit tests for easy_acumatica.models.filters (Filter & QueryOptions).
"""

from easy_acumatica.models.filter_builder import Filter, QueryOptions


# ---------------------------------------------------------------------------
# Filter helper
# ---------------------------------------------------------------------------
def test_eq_literal_string():
    f = Filter().eq("Name", "O'Neil")
    assert f.build() == "Name eq 'O''Neil'"          # single-quote escaped


def test_comparison_ops():
    assert Filter().gt("Age", 21).build() == "Age gt 21"
    assert Filter().lt("Age", 65).build() == "Age lt 65"


def test_contains_helper():
    expr = Filter().contains("DisplayName", "Ann").build()
    assert expr == "substringof('Ann',DisplayName)"


def test_compound_and_or():
    f1 = Filter().eq("A", 1)
    f2 = Filter().eq("B", 2)
    assert f1.and_(f2).build() == "A eq 1 and B eq 2"
    assert f1.or_(f2).build() == "A eq 1 or B eq 2"


def test_filter_is_immutable():
    base = Filter().eq("X", 1)
    new = base.and_(Filter().eq("Y", 2))
    assert base.build() == "X eq 1"          # unchanged
    assert new.build() == "X eq 1 and Y eq 2"


def test_cf_custom_field_reference():
    cf_expr = Filter.cf("Decimal", "Document", "CuryBalanceWOTotal")
    assert cf_expr == "cf.Decimal(f='Document.CuryBalanceWOTotal')"


# ---------------------------------------------------------------------------
# QueryOptions
# ---------------------------------------------------------------------------
def test_to_params_full():
    flt = Filter().eq("ContactID", 1)
    opts = QueryOptions(
        filter=flt,
        expand=["Activities", "Address"],
        select=["ContactID", "DisplayName"],
        top=10,
        skip=5,
        custom=["ItemSettings.UsrRepairItemType"]
    )
    params = opts.to_params()
    assert params == {
        "$filter": "ContactID eq 1",
        "$expand": "Activities,Address",
        "$select": "ContactID,DisplayName",
        "$top": "10",
        "$skip": "5",
        "$custom": "ItemSettings.UsrRepairItemType",
    }


def test_to_params_with_plain_string_filter():
    opts = QueryOptions(filter="Status eq 'Active'")
    assert opts.to_params() == {"$filter": "Status eq 'Active'"}


def test_to_params_empty():
    assert QueryOptions().to_params() == {}


def test_select_and_expand_joining():
    opts = QueryOptions(select=["A", "B"], expand=["X", "Y"])
    p = opts.to_params()
    assert p["$select"] == "A,B"
    assert p["$expand"] == "X,Y"


def test_top_and_skip_types():
    opts = QueryOptions(top=1, skip=0)
    params = opts.to_params()
    assert params["$top"] == "1" and params["$skip"] == "0"


def test_queryoptions_custom_alone():
    opts = QueryOptions(custom=["Foo.Bar", "Baz.Quux"])
    assert opts.to_params() == {"$custom": "Foo.Bar,Baz.Quux"}


def test_to_params_with_custom_and_others():
    flt = Filter().eq("ContactID", 102210)
    opts = QueryOptions(
        filter=flt,
        top=5,
        select=["ContactID", "DisplayName"],
        custom=["ItemSettings.UsrRepairItemType"]
    )
    params = opts.to_params()
    assert params == {
        "$filter": "ContactID eq 102210",
        "$select": "ContactID,DisplayName",
        "$top": "5",
        "$custom": "ItemSettings.UsrRepairItemType",
    }
