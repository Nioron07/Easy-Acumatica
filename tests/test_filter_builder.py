# tests/test_filters.py
"""
Unit tests for easy_acumatica.models.filters:
  - Filter
  - QueryOptions
  - MathBuilder
  - DateBuilder
  - StringBuilder

Covers all operators/functions and builder→filter integration.
"""

from easy_acumatica.models.filter_builder import (
    Filter,
    QueryOptions,
    MathBuilder,
    DateBuilder,
    StringBuilder,
)


# ---------------------------------------------------------------------------
# Filter – basic ops
# ---------------------------------------------------------------------------
def test_eq_literal_string():
    f = Filter().eq("Name", "O'Neil")
    assert f.build() == "Name eq 'O''Neil'"


def test_comparison_ops_all():
    assert Filter().gt("A", 1).build() == "A gt 1"
    assert Filter().lt("A", 2).build() == "A lt 2"
    assert Filter().ge("A", 3).build() == "A ge 3"
    assert Filter().le("A", 4).build() == "A le 4"


def test_contains_starts_ends_helpers():
    c = Filter().contains("X", "sub").build()
    s = Filter().starts_with("X", "pre").build()
    e = Filter().ends_with("X", "suf").build()
    assert c == "substringof('sub',X)"
    assert s == "startswith(X,'pre')"
    assert e == "endswith(X,'suf')"


def test_logical_and_or_not_immutable():
    f1 = Filter().eq("A", 1)
    f2 = Filter().eq("B", 2)
    combined = f1.and_(f2)
    assert combined.build() == "(A eq 1 and B eq 2)"
    assert f1.build() == "A eq 1"  # immutability
    assert f1.or_(f2).build() == "(A eq 1 or B eq 2)"
    assert Filter().not_(f1).build() == "not (A eq 1)"


# ---------------------------------------------------------------------------
# MathBuilder – arithmetic and math functions
# ---------------------------------------------------------------------------
def test_mathbuilder_arithmetic():
    mb = MathBuilder.field("P").add(5).sub(2).mul(3).div(4).mod(2)
    # (((((P add 5) sub 2) mul 3) div 4) mod 2)
    assert mb.expr.count('(') == 5
    assert "P add 5" in mb.expr
    assert mb.expr.endswith(" mod 2)")


def test_mathbuilder_round_floor_ceiling():
    m = MathBuilder.field("F")
    assert m.round().expr == "round(F)"
    assert m.floor().expr == "floor(F)"
    assert m.ceiling().expr == "ceiling(F)"


# ---------------------------------------------------------------------------
# DateBuilder – date extraction
# ---------------------------------------------------------------------------
def test_datebuilder_fields():
    expr = DateBuilder.day("BirthDate")
    assert str(expr) == "day(BirthDate)"

    expr = DateBuilder.month("BirthDate")
    assert str(expr) == "month(BirthDate)"
    
    expr = DateBuilder.year("BirthDate")
    assert str(expr) == "year(BirthDate)"
    
    expr = DateBuilder.hour("BirthDate")
    assert str(expr) == "hour(BirthDate)"
    
    expr = DateBuilder.minute("BirthDate")
    assert str(expr) == "minute(BirthDate)"
    
    expr = DateBuilder.second("BirthDate")
    assert str(expr) == "second(BirthDate)"


# ---------------------------------------------------------------------------
# StringBuilder – string functions
# ---------------------------------------------------------------------------
def test_stringbuilder_length_indexof():
    sb = StringBuilder.field("S")
    assert sb.length().expr == "length(S)"
    assert sb.indexof("foo").expr == "indexof(S,'foo')"
    # chaining with raw
    raw = StringBuilder.raw("concat(A,'B')")
    assert raw.indexof(raw).expr == "indexof(concat(A,'B'),concat(A,'B'))"


def test_stringbuilder_replace_and_substring():
    sb = StringBuilder.field("S").replace("x", "y")
    assert sb.expr == "replace(S,'x','y')"
    # substring single
    sub1 = StringBuilder.field("T").substring(1)
    assert sub1.expr == "substring(T,1)"
    # substring with length
    sub2 = StringBuilder.field("T").substring(1, 2)
    assert sub2.expr == "substring(T,1,2)"


def test_stringbuilder_case_trim_concat():
    sb = StringBuilder.field("C")
    assert sb.tolower().expr == "tolower(C)"
    assert sb.toupper().expr == "toupper(C)"
    assert sb.trim().expr == "trim(C)"
    # concat literal and builder
    c1 = sb.concat("Z")
    assert c1.expr == "concat(C,'Z')"
    c2 = sb.concat(StringBuilder.field("D"))
    assert c2.expr == "concat(C,D)"


# ---------------------------------------------------------------------------
# Builder → Filter integration
# ---------------------------------------------------------------------------
def test_mathbuilder_in_filter():
    expr = MathBuilder.field("Price").add(5)
    f = Filter().gt(expr, 100)
    assert f.build() == "(Price add 5) gt 100"


def test_datebuilder_in_filter():
    expr = DateBuilder.day("BirthDate")
    f = Filter().eq(expr, 15)
    assert f.build() == "day(BirthDate) eq 15"


def test_stringbuilder_in_filter_contains_starts_ends():
    sb = StringBuilder.field("Name").replace("old", "new")
    f1 = Filter().contains("X", sb.expr)  # as raw substr
    assert f1.build() == f"substringof('{sb.expr}',X)"
    f2 = Filter().starts_with("X", sb)
    f3 = Filter().ends_with("X", sb)
    assert f2.build() == f"startswith(X,{sb.expr})"
    assert f3.build() == f"endswith(X,{sb.expr})"


# ---------------------------------------------------------------------------
# QueryOptions – param serialization
# ---------------------------------------------------------------------------
def test_queryoptions_full_and_empty():
    flt = Filter().eq("C", 3)
    opts = QueryOptions(
        filter=flt,
        expand=["E1"],
        select=["S1"],
        top=7,
        skip=2,
        custom=["CF1"]
    )
    params = opts.to_params()
    assert params == {
        "$filter": "C eq 3",
        "$expand": "E1",
        "$select": "S1",
        "$top": "7",
        "$skip": "2",
        "$custom": "CF1",
    }
    # empty
    assert QueryOptions().to_params() == {}
