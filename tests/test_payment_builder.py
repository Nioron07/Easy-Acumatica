# tests/models/test_payment_builder.py

import pytest
from easy_acumatica.models.payment_builder import PaymentBuilder


def test_builder_methods_chain():
    """Tests that all setter methods are chainable."""
    builder = (
        PaymentBuilder()
        .cash_account("10250ST")
        .customer_id("FRUITICO")
        .hold(False)
        .payment_amount(235.27)
        .type("Payment")
        .add_document_to_apply("INV", "00001")
        .add_order_to_apply("SO", "00002")
        .add_credit_card_transaction("123", "Auth", "abc")
    )
    assert isinstance(builder, PaymentBuilder)


def test_to_body_builds_correct_simple_payload():
    """Tests that the to_body method constructs the correct dictionary for simple fields."""
    builder = (
        PaymentBuilder()
        .cash_account("10250ST")
        .customer_id("FRUITICO")
        .hold(False)
        .payment_amount(235.27)
        .type("Payment")
    )
    payload = builder.to_body()
    expected = {
        "CashAccount": {"value": "10250ST"},
        "CustomerID": {"value": "FRUITICO"},
        "Hold": {"value": False},
        "PaymentAmount": {"value": 235.27},
        "Type": {"value": "Payment"},
    }
    assert payload == expected


def test_to_body_with_documents_to_apply():
    """Tests that documents to apply are correctly added to the payload."""
    builder = (
        PaymentBuilder()
        .add_document_to_apply("INV", "000002", doc_line_nbr=1)
        .add_document_to_apply("CRN", "000003")
    )
    payload = builder.to_body()
    expected_docs = [
        {
            "DocType": {"value": "INV"},
            "ReferenceNbr": {"value": "000002"},
            "DocLineNbr": {"value": "1"},
        },
        {
            "DocType": {"value": "CRN"},
            "ReferenceNbr": {"value": "000003"},
        },
    ]
    assert "DocumentsToApply" in payload
    assert payload["DocumentsToApply"] == expected_docs


def test_to_body_with_orders_to_apply():
    """Tests that orders to apply are correctly added to the payload."""
    builder = (
        PaymentBuilder()
        .add_order_to_apply("SO", "000036")
    )
    payload = builder.to_body()
    expected_orders = [
        {
            "OrderType": {"value": "SO"},
            "OrderNbr": {"value": "000036"},
        }
    ]
    assert "OrdersToApply" in payload
    assert payload["OrdersToApply"] == expected_orders


def test_to_body_with_credit_card_transactions():
    """Tests that credit card transactions are correctly added to the payload."""
    builder = (
        PaymentBuilder()
        .add_credit_card_transaction(
            tran_nbr="112233",
            tran_type="Authorize Only",
            auth_nbr="abc123",
            needs_validation=False
        )
    )
    payload = builder.to_body()
    expected_cc = [
        {
            "TranNbr": {"value": "112233"},
            "TranType": {"value": "Authorize Only"},
            "AuthNbr": {"value": "abc123"},
            "NeedsValidation": {"value": False},
        }
    ]
    assert "CreditCardTransactionInfo" in payload
    assert payload["CreditCardTransactionInfo"] == expected_cc


def test_to_body_with_all_lists():
    """Tests a complex builder with all types of lists."""
    builder = (
        PaymentBuilder()
        .customer_id("COMPLEX")
        .add_document_to_apply("INV", "INV01")
        .add_order_to_apply("SO", "SO01")
        .add_credit_card_transaction("445566", "Capture", "xyz789")
    )
    payload = builder.to_body()
    assert payload["CustomerID"] == {"value": "COMPLEX"}
    assert "DocumentsToApply" in payload and len(payload["DocumentsToApply"]) == 1
    assert "OrdersToApply" in payload and len(payload["OrdersToApply"]) == 1
    assert "CreditCardTransactionInfo" in payload and len(payload["CreditCardTransactionInfo"]) == 1


def test_to_body_returns_fresh_copy():
    """Ensures that mutating the returned body doesn't affect the builder."""
    builder = PaymentBuilder().customer_id("CUST01").add_document_to_apply("INV", "1")
    body1 = builder.to_body()
    body1["CustomerID"]["value"] = "MODIFIED"
    body1["DocumentsToApply"][0]["ReferenceNbr"]["value"] = "MODIFIED_REF"

    body2 = builder.to_body()
    assert body2["CustomerID"]["value"] == "CUST01"
    assert body2["DocumentsToApply"][0]["ReferenceNbr"]["value"] == "1"

