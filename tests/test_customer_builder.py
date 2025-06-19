# tests/test_customer_builder.py

import pytest

from easy_acumatica.models.customer_builder import CustomerBuilder


def test_set_arbitrary_field():
    cb = CustomerBuilder().set("Foo", 123)
    assert cb.to_body() == {"Foo": {"value": 123}}


def test_convenience_methods_chain():
    cb = (
        CustomerBuilder()
        .customer_id("CUST01")
        .customer_name("Test Customer")
        .customer_class("DEFAULT")
    )
    assert cb.to_body() == {
        "CustomerID": {"value": "CUST01"},
        "CustomerName": {"value": "Test Customer"},
        "CustomerClass": {"value": "DEFAULT"},
    }


def test_set_and_convenience_combination():
    cb = CustomerBuilder().customer_id("C2").set("CreditLimit", 1000.0)
    assert cb.to_body() == {
        "CustomerID": {"value": "C2"},
        "CreditLimit": {"value": 1000.0},
    }


def test_overwriting_field_value():
    cb = CustomerBuilder().set("Foo", "first").set("Foo", "second")
    assert cb.to_body() == {"Foo": {"value": "second"}}


def test_to_body_returns_fresh_copy():
    cb = CustomerBuilder().set("A", "a")
    body1 = cb.to_body()
    body1["A"]["value"] = "modified"
    body2 = cb.to_body()
    # body2 must not reflect the change to body1
    assert body2["A"]["value"] == "a"


def test_chaining_returns_self():
    cb = CustomerBuilder()
    returned = cb.set("X", "x").customer_id("C1")
    # ensure that methods return the same builder instance
    assert returned is cb
