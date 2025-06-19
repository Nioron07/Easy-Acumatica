# tests/test_inquiry_options.py

from easy_acumatica.models.inquiry_builder import InquiryBuilder

def test_chaining_returns_self():
    opts = InquiryBuilder()
    # both methods should return the same instance for chaining
    assert opts.param("Foo", 1) is opts
    assert opts.expand("Bar") is opts

def test_param_and_to_body_single():
    opts = InquiryBuilder().param("InventoryID", "ABC123")
    assert opts.to_body() == {"InventoryID": {"value": "ABC123"}}

def test_param_overwrite():
    opts = InquiryBuilder()
    opts.param("X", 1)
    opts.param("X", 2)
    # later .param should overwrite earlier
    assert opts.to_body() == {"X": {"value": 2}}

def test_to_body_empty_parameters():
    opts = InquiryBuilder()
    # with no .param calls, to_body returns an empty dict
    assert opts.to_body() == {}

def test_expand_and_to_query_params_single():
    opts = InquiryBuilder().expand("Results")
    assert opts.to_query_params() == {"$expand": "Results"}

def test_expand_variadic_and_ordering():
    opts = InquiryBuilder().expand("A", "B", "C")
    # order should be preserved
    assert opts.to_query_params() == {"$expand": "A,B,C"}

def test_multiple_expand_calls_concat():
    opts = InquiryBuilder()
    opts.expand("One")
    opts.expand("Two", "Three")
    # expands should accumulate in definition order
    assert opts.to_query_params() == {"$expand": "One,Two,Three"}

def test_to_query_params_empty_expand():
    opts = InquiryBuilder()
    # with no .expand, to_query_params returns an empty dict
    assert opts.to_query_params() == {}
