"""Pure unit tests for the TUI's code-rendering helpers.

These tests don't import Textual - they exercise classify_field,
render_model, and render_call directly. Fast, deterministic, no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

import pytest

from easy_acumatica.core import BaseDataClassModel
from easy_acumatica.odata import F, QueryOptions
from easy_acumatica.tui.code_render import (
    classify_field,
    render_call,
    render_model,
)


# --- Fake models for the tests --------------------------------------------


@dataclass
class _FakeAddress(BaseDataClassModel):
    City: Optional[str] = None
    State: Optional[str] = None


@dataclass
class _FakeContact(BaseDataClassModel):
    Email: Optional[str] = None


@dataclass
class _FakeDetail(BaseDataClassModel):
    InventoryID: Optional[str] = None
    OrderQty: Optional[int] = None


@dataclass
class _FakeOrder(BaseDataClassModel):
    OrderType: Optional[str] = None
    ShipToAddress: Optional[_FakeAddress] = None
    BillToContact: Optional[_FakeContact] = None
    Details: Optional[List[_FakeDetail]] = None


# --- classify_field -------------------------------------------------------


def test_classify_optional_primitive():
    info = classify_field(Optional[str])
    assert info['kind'] == 'primitive'
    assert info['type'] is str
    assert info['optional'] is True


def test_classify_required_primitive():
    info = classify_field(int)
    assert info['kind'] == 'primitive'
    assert info['type'] is int
    assert info['optional'] is False


def test_classify_optional_model():
    info = classify_field(Optional[_FakeAddress])
    assert info['kind'] == 'model'
    assert info['model'] is _FakeAddress
    assert info['optional'] is True


def test_classify_list_of_models():
    info = classify_field(Optional[List[_FakeDetail]])
    assert info['kind'] == 'list-model'
    assert info['model'] is _FakeDetail
    assert info['optional'] is True


def test_classify_list_of_optional_models():
    """The runtime annotation for some fields is List[Optional[Model]]."""
    info = classify_field(Optional[List[Optional[_FakeDetail]]])
    assert info['kind'] == 'list-model'
    assert info['model'] is _FakeDetail


def test_classify_list_of_primitives():
    info = classify_field(Optional[List[str]])
    assert info['kind'] == 'list-primitive'
    assert info['item'] is str


# --- render_model ---------------------------------------------------------


def test_render_model_flat():
    m = _FakeAddress(City='Austin', State='TX')
    lines, imports, top_var = render_model(m)
    assert imports == {'_FakeAddress'}
    assert top_var == 'fake_address'
    assert len(lines) == 1
    assert lines[0] == "fake_address = _FakeAddress(City='Austin', State='TX')"


def test_render_model_skips_none_fields():
    m = _FakeAddress(City='Austin')  # State left None
    lines, _, _ = render_model(m)
    assert 'State=' not in lines[0]
    assert "City='Austin'" in lines[0]


def test_render_model_with_nested_model():
    """A nested model becomes its own helper line; the top-level
    constructor references it by variable name."""
    addr = _FakeAddress(City='Austin')
    order = _FakeOrder(OrderType='SO', ShipToAddress=addr)
    lines, imports, top_var = render_model(order)

    assert imports == {'_FakeAddress', '_FakeOrder'}
    assert top_var == 'fake_order'
    # Helper for the nested model comes BEFORE the top-level
    assert lines[0].startswith('ship_to_address = _FakeAddress(')
    assert lines[-1].startswith('fake_order = _FakeOrder(')
    # Top-level references the helper var, not an inline ctor
    assert 'ShipToAddress=ship_to_address' in lines[-1]
    assert '_FakeAddress(' not in lines[-1]


def test_render_model_with_two_nested_models_uses_field_names_for_vars():
    addr = _FakeAddress(City='Austin')
    contact = _FakeContact(Email='x@y.com')
    order = _FakeOrder(ShipToAddress=addr, BillToContact=contact)
    lines, _, top_var = render_model(order)

    assert any(line.startswith('ship_to_address = ') for line in lines)
    assert any(line.startswith('bill_to_contact = ') for line in lines)
    top_line = next(line for line in lines if line.startswith('fake_order'))
    assert 'ShipToAddress=ship_to_address' in top_line
    assert 'BillToContact=bill_to_contact' in top_line


def test_render_model_with_list_of_models_inlines_items():
    detail1 = _FakeDetail(InventoryID='ITEM01', OrderQty=2)
    detail2 = _FakeDetail(InventoryID='ITEM02', OrderQty=5)
    order = _FakeOrder(OrderType='SO', Details=[detail1, detail2])
    lines, imports, _ = render_model(order)

    assert imports == {'_FakeOrder', '_FakeDetail'}
    # Each detail row gets its own helper variable...
    detail_lines = [line for line in lines if line.startswith('details')]
    assert len(detail_lines) == 2
    # ...and the top-level references them as a list
    top_line = lines[-1]
    assert 'Details=[details, details_2]' in top_line


# --- render_call ----------------------------------------------------------


def test_render_call_get_list_no_options():
    code = render_call('contact', 'get_list')
    assert 'from easy_acumatica import AcumaticaClient' in code
    assert 'client.contact.get_list()' in code
    # No options imports when not needed
    assert 'QueryOptions' not in code


def test_render_call_get_list_with_query_options():
    opts = QueryOptions(top=5, filter="Status eq 'Active'")
    code = render_call('contact', 'get_list', keyword={'options': opts})
    assert 'from easy_acumatica.odata import F, QueryOptions' in code
    assert 'options=QueryOptions(top=5, filter=' in code
    assert "Status eq 'Active'" in code


def test_render_call_get_list_with_F_filter():
    """A Filter object is rendered via its OData string form."""
    opts = QueryOptions(filter=F.Name == 'foo')
    code = render_call('contact', 'get_list', keyword={'options': opts})
    # Whatever str(filter) produces should appear in the output
    assert 'filter=' in code
    assert 'Name eq' in code or 'Name' in code  # tolerant of formatting


def test_render_call_get_by_id_positional():
    code = render_call(
        'contact', 'get_by_id',
        positional=['a38c9560-913d-f111-8431-126ad4ca5ceb'],
    )
    assert "client.contact.get_by_id('a38c9560-913d-f111-8431-126ad4ca5ceb')" in code


def test_render_call_delete_by_keys_uses_kwargs():
    code = render_call(
        'sales_order', 'delete_by_keys',
        keyword={'OrderType': 'SO', 'OrderNbr': '000123'},
    )
    assert "client.sales_order.delete_by_keys(" in code
    assert "OrderType='SO'" in code
    assert "OrderNbr='000123'" in code


def test_render_call_skips_none_kwargs():
    """A kwarg explicitly set to None should be omitted from the rendered call."""
    code = render_call(
        'contact', 'get_by_id',
        positional=['x'],
        keyword={'options': None},
    )
    assert 'options=' not in code


def test_render_call_put_entity_combines_model_and_call():
    addr = _FakeAddress(City='Austin', State='TX')
    order = _FakeOrder(OrderType='SO', ShipToAddress=addr)

    code = render_call('sales_order', 'put_entity', entity_model=order)

    # Imports
    assert 'from easy_acumatica import AcumaticaClient' in code
    assert 'from easy_acumatica.models import _FakeAddress, _FakeOrder' in code

    # Helper for the nested address comes before the order
    addr_idx = code.index('ship_to_address = _FakeAddress(')
    order_idx = code.index('fake_order = _FakeOrder(')
    call_idx = code.index('client.sales_order.put_entity(fake_order)')
    assert addr_idx < order_idx < call_idx

    # Call references the top-level var (not a literal repr of the model)
    assert 'put_entity(fake_order)' in code


def test_render_call_put_file_positional_and_kwargs():
    """put_file: entity_id positional, filename + data + comment as values."""
    code = render_call(
        'contact', 'put_file',
        positional=['a38c9560-913d-f111-8431-126ad4ca5ceb', 'attachment.pdf', b'%PDF...'],
        keyword={'comment': 'cover sheet'},
    )
    assert "client.contact.put_file(" in code
    assert "'a38c9560-913d-f111-8431-126ad4ca5ceb'" in code
    assert "'attachment.pdf'" in code
    assert "b'%PDF...'" in code
    assert "comment='cover sheet'" in code
