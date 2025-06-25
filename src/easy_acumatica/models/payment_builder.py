# src/easy_acumatica/models/payment_builder.py

from __future__ import annotations
from typing import Any, Dict, List, Optional
import copy


class PaymentBuilder:
    """
    Fluent builder for the JSON payload to create or update a Payment.
    Each field is wrapped as {"value": ...} to match Acumatica's contract-based API.
    """

    def __init__(self) -> None:
        self._fields: Dict[str, Any] = {}
        self._documents_to_apply: List[Dict[str, Dict[str, Any]]] = []
        self._orders_to_apply: List[Dict[str, Dict[str, Any]]] = []
        self._credit_card_transactions: List[Dict[str, Dict[str, Any]]] = []

    def set(self, field: str, value: Any) -> PaymentBuilder:
        """
        Set any arbitrary field on the Payment payload.
        Overwrites previous value if called twice.
        """
        self._fields[field] = {"value": value}
        return self
        
    def add_document_to_apply(self, doc_type: str, reference_nbr: str, doc_line_nbr: Optional[int] = None) -> PaymentBuilder:
        """
        Adds a document (like an invoice) to be paid.
        
        Args:
            doc_type (str): The type of the document (e.g., 'INV').
            reference_nbr (str): The reference number of the document.
            doc_line_nbr (int, optional): The specific line number of the document.
        """
        doc = {
            "DocType": {"value": doc_type},
            "ReferenceNbr": {"value": reference_nbr}
        }
        if doc_line_nbr is not None:
            doc["DocLineNbr"] = {"value": str(doc_line_nbr)}
            
        self._documents_to_apply.append(doc)
        return self

    def add_order_to_apply(self, order_type: str, order_nbr: str) -> PaymentBuilder:
        """
        Adds a sales order to be paid.
        
        Args:
            order_type (str): The type of the order (e.g., 'SO').
            order_nbr (str): The order number.
        """
        order = {
            "OrderType": {"value": order_type},
            "OrderNbr": {"value": order_nbr}
        }
        self._orders_to_apply.append(order)
        return self

    def add_credit_card_transaction(
        self,
        tran_nbr: str,
        tran_type: str,
        auth_nbr: str,
        needs_validation: bool = True
    ) -> PaymentBuilder:
        """
        Adds imported credit card transaction details to the payment.
        
        Args:
            tran_nbr (str): The transaction ID from the processing center.
            tran_type (str): The transaction type (e.g., 'Authorize Only').
            auth_nbr (str): The authorization number from the processing center.
            needs_validation (bool): If True, payment status will be 'Pending Processing'.
        """
        cc_tran = {
            "TranNbr": {"value": tran_nbr},
            "TranType": {"value": tran_type},
            "AuthNbr": {"value": auth_nbr},
            "NeedsValidation": {"value": needs_validation},
        }
        self._credit_card_transactions.append(cc_tran)
        return self

    def cash_account(self, account: str) -> PaymentBuilder:
        """Shortcut for .set('CashAccount', account)."""
        return self.set("CashAccount", account)

    def customer_id(self, cust_id: str) -> PaymentBuilder:
        """Shortcut for .set('CustomerID', cust_id)."""
        return self.set("CustomerID", cust_id)

    def hold(self, flag: bool) -> PaymentBuilder:
        """Shortcut for .set('Hold', flag)."""
        return self.set("Hold", flag)

    def payment_amount(self, amount: float) -> PaymentBuilder:
        """Shortcut for .set('PaymentAmount', amount)."""
        return self.set("PaymentAmount", amount)

    def type(self, payment_type: str) -> PaymentBuilder:
        """Shortcut for .set('Type', payment_type)."""
        return self.set("Type", payment_type)

    def payment_method(self, method_id: str) -> PaymentBuilder:
        """Shortcut for .set('PaymentMethod', method_id)."""
        return self.set("PaymentMethod", method_id)

    def payment_ref(self, reference: str) -> PaymentBuilder:
        """Shortcut for .set('PaymentRef', reference)."""
        return self.set("PaymentRef", reference)

    def location_id(self, location: str) -> PaymentBuilder:
        """Shortcut for .set('CustomerLocationID', location)."""
        return self.set("CustomerLocationID", location)
    
    def application_date(self, date: str) -> PaymentBuilder:
        """Shortcut for .set('ApplicationDate', date) in 'YYYY-MM-DD' format."""
        return self.set("ApplicationDate", date)

    def description(self, text: str) -> PaymentBuilder:
        """Shortcut for .set('Description', text)."""
        return self.set("Description", text)

    def currency_id(self, currency: str) -> PaymentBuilder:
        """Shortcut for .set('CurrencyID', currency)."""
        return self.set("CurrencyID", currency)
    
    def branch(self, branch_id: str) -> PaymentBuilder:
        """Shortcut for .set('Branch', branch_id)."""
        return self.set("Branch", branch_id)
    
    def external_ref(self, ref: str) -> PaymentBuilder:
        """Shortcut for .set('ExternalRef', ref)."""
        return self.set("ExternalRef", ref)

    # --- Credit Card Fields ---

    def card_account_nbr(self, nbr: str) -> PaymentBuilder:
        """Shortcut for .set('CardAccountNbr', nbr)."""
        return self.set("CardAccountNbr", nbr)

    def is_cc_payment(self, flag: bool) -> PaymentBuilder:
        """Shortcut for .set('IsCCPayment', flag)."""
        return self.set("IsCCPayment", flag)

    def is_new_card(self, flag: bool) -> PaymentBuilder:
        """Shortcut for .set('IsNewCard', flag)."""
        return self.set("IsNewCard", flag)
    
    def processing_center_id(self, pcid: str) -> PaymentBuilder:
        """Shortcut for .set('ProcessingCenterID', pcid)."""
        return self.set("ProcessingCenterID", pcid)

    def save_card(self, flag: bool) -> PaymentBuilder:
        """Shortcut for .set('SaveCard', flag)."""
        return self.set("SaveCard", flag)

    def to_body(self) -> Dict[str, Any]:
        """
        Return a fresh dict suitable for the PUT body. This combines the main fields
        with the lists of documents and orders to apply.
        """
        # Start with a deep copy of the main fields to ensure nested dicts are copied
        body = copy.deepcopy(self._fields)

        # Add deep copies of the lists if they are not empty
        if self._documents_to_apply:
            body['DocumentsToApply'] = copy.deepcopy(self._documents_to_apply)
        
        if self._orders_to_apply:
            body['OrdersToApply'] = copy.deepcopy(self._orders_to_apply)

        if self._credit_card_transactions:
            body['CreditCardTransactionInfo'] = copy.deepcopy(self._credit_card_transactions)
            
        return body
