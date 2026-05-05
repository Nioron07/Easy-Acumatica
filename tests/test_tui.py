"""Smoke tests for the easy_acumatica TUI.

These run against Textual's in-memory pilot harness (``App.run_test()``),
not a real terminal. They cover user-visible screens with an injected fake
client so nothing touches the network or the real ``.env``.
"""
from __future__ import annotations

import sys
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from easy_acumatica.tui.app import AcumaticaTUI
from easy_acumatica.tui.screens import (
    CredentialsScreen,
    LoadingScreen,
    MainScreen,
    StartScreen,
)


# --- Fake client injected in place of AcumaticaClient -------------------


class _FakeService:
    """Minimal stand-in for a generated service with the 4 GET methods."""

    def __init__(self, name: str):
        self.name = name
        self.entity_name = name
        self.calls: List[tuple] = []

    # Signatures use **kwargs so the fake records exactly what the caller
    # passed - important for asserting the TUI doesn't sneak in options=None
    # for single-record fetches.

    def get_list(self, *args, **kwargs):
        self.calls.append(('get_list', args, kwargs))
        return {'value': [{'ID': '1', 'Name': 'Alpha'}, {'ID': '2', 'Name': 'Beta'}]}

    def get_by_id(self, entity_id, *args, **kwargs):
        self.calls.append(('get_by_id', (entity_id, *args), kwargs))
        return {'ID': entity_id, 'Name': 'Found', 'Service': self.name}

    def get_by_keys(self, *args, **kwargs):
        self.calls.append(('get_by_keys', args, kwargs))
        return {'Service': self.name, 'Keys': dict(kwargs)}

    def get_ad_hoc_schema(self, *args, **kwargs):
        self.calls.append(('get_ad_hoc_schema', args, kwargs))
        return {'fields': {'ID': {'type': 'String'}}}

    def get_files(self, entity_id, *args, **kwargs):
        self.calls.append(('get_files', (entity_id, *args), kwargs))
        return [
            {'id': 'file-1', 'filename': 'attachment.pdf'},
            {'id': 'file-2', 'filename': 'photo.jpg'},
        ]

    def delete_by_id(self, entity_id, *args, **kwargs):
        self.calls.append(('delete_by_id', (entity_id, *args), kwargs))
        return True

    def delete_by_keys(self, *args, **kwargs):
        self.calls.append(('delete_by_keys', args, kwargs))
        return True

    def put_entity(self, *args, **kwargs):
        self.calls.append(('put_entity', args, kwargs))
        return {'id': 'created', 'echo': args[0] if args else None}

    def put_file(self, entity_id, filename, data, *args, **kwargs):
        self.calls.append(('put_file', (entity_id, filename, data, *args), kwargs))
        return None


class _FakeInquiriesService:
    """Stand-in for the Inquiries service with dynamically attached methods."""

    def __init__(self, inquiry_methods: List[str]):
        self.entity_name = 'Inquiries'
        self.calls: List[tuple] = []
        for method_name in inquiry_methods:
            self._attach_inquiry(method_name)

    def _attach_inquiry(self, method_name: str) -> None:
        def _inquiry(self, options=None, _name=method_name):
            self.calls.append((_name, (), {'options': options}))
            return {
                'value': [
                    {'inquiry': _name, 'row': 1},
                    {'inquiry': _name, 'row': 2},
                ]
            }
        _inquiry.__name__ = method_name
        _inquiry.__doc__ = f'Generic Inquiry: {method_name}.'
        setattr(self, method_name, _inquiry.__get__(self, self.__class__))


class _FakeClient:
    def __init__(
        self,
        *,
        services: List[str],
        models: List[str],
        inquiries: List[str] = None,
    ):
        self.base_url = 'https://fake.example.com'
        self.tenant = 'FAKE'
        self.endpoint_name = 'Default'
        self.endpoint_version = '24.200.001'
        self._services = services
        self._models = models
        self._inquiries = list(inquiries or [])
        self._service_instances = {name: _FakeService(name) for name in services}
        if self._inquiries:
            self._service_instances['Inquiries'] = _FakeInquiriesService(self._inquiries)
        self.logout_called = False
        self.close_called = False
        self.refresh_called = 0

    def list_services(self) -> List[str]:
        return list(self._services)

    def list_models(self) -> List[str]:
        return list(self._models)

    def list_inquiries(self) -> List[str]:
        return list(self._inquiries)

    def get_inquiry_info(self, name: str) -> Dict[str, Any]:
        if name not in self._inquiries:
            raise ValueError(f"Inquiry '{name}' not found.")
        method = getattr(self._service_instances['Inquiries'], name)
        return {
            'name': name,
            'method_name': name,
            'doc': method.__doc__,
        }

    def get_service_info(self, name: str) -> Dict[str, Any]:
        if name not in self._services:
            raise ValueError(f"Service '{name}' not found.")
        return {
            'name': name,
            'entity_name': name,
            'endpoint_name': 'Default',
            'client_attribute': name.lower(),
            'methods': [{'name': 'get_list', 'docstring': 'List entities.'}],
            'method_count': 1,
        }

    def get_model_info(self, name: str) -> Dict[str, Any]:
        if name not in self._models:
            raise ValueError(f"Model '{name}' not found.")
        return {
            'name': name,
            'field_count': 2,
            'docstring': f'The {name} data model.',
            'fields': {
                'id': {'type': 'str', 'required': True},
                'name': {'type': 'Optional[str]', 'required': False},
            },
        }

    def refresh_schema(self) -> None:
        self.refresh_called += 1

    def logout(self) -> None:
        self.logout_called = True

    def close(self) -> None:
        self.close_called = True


def _make_app(
    *,
    services: List[str] = None,
    models: List[str] = None,
    inquiries: List[str] = None,
) -> AcumaticaTUI:
    services = services or ['Account', 'Bill', 'Contact']
    models = models or ['Address', 'Person']
    fake = _FakeClient(services=services, models=models, inquiries=inquiries)

    def factory(source, credentials):
        return fake

    return AcumaticaTUI(client_factory=factory)


# --- 1. Start screen ----------------------------------------------------


@pytest.mark.asyncio
async def test_start_screen_renders():
    app = _make_app()
    async with app.run_test() as pilot:
        # StartScreen is on top
        assert isinstance(app.screen, StartScreen)
        # Three buttons exist
        from textual.widgets import Button
        buttons = app.screen.query(Button)
        ids = {b.id for b in buttons}
        assert {'use-env', 'use-manual', 'quit'}.issubset(ids)


@pytest.mark.asyncio
async def test_start_screen_quit_button_exits():
    app = _make_app()
    async with app.run_test() as pilot:
        await pilot.click('#quit')
        await pilot.pause()
    # App has exited cleanly (no assertion - run_test returns when app stops)


# --- 2. Credentials screen ---------------------------------------------


@pytest.mark.asyncio
async def test_credentials_screen_validates_required_fields():
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.click('#use-manual')
        await pilot.pause()
        assert isinstance(app.screen, CredentialsScreen)

        # Press Connect via the widget API (avoids mouse/layout coord issues).
        from textual.widgets import Button, Static
        app.screen.query_one('#connect', Button).press()
        await pilot.pause()

        err = app.screen.query_one('#creds-error', Static)
        assert 'Missing' in str(err.render())
        assert isinstance(app.screen, CredentialsScreen)


@pytest.mark.asyncio
async def test_credentials_screen_submits_valid_form():
    app = _make_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.click('#use-manual')
        await pilot.pause()

        from textual.widgets import Button, Input
        screen = app.screen
        screen.query_one('#f-base-url', Input).value = 'https://x.example.com'
        screen.query_one('#f-username', Input).value = 'u'
        screen.query_one('#f-password', Input).value = 'p'
        screen.query_one('#f-tenant', Input).value = 't'

        screen.query_one('#connect', Button).press()
        await pilot.pause()
        assert not isinstance(app.screen, CredentialsScreen)


# --- 3. Loading + main screen transition --------------------------------


@pytest.mark.asyncio
async def test_env_path_leads_to_main_screen_with_services():
    app = _make_app(services=['Account', 'Bill'], models=['Address'])
    async with app.run_test() as pilot:
        await pilot.click('#use-env')
        # Wait for the worker thread to complete and the screen to switch.
        await pilot.pause()
        # Allow the worker to finish (poll up to a few cycles).
        for _ in range(20):
            if isinstance(app.screen, MainScreen):
                break
            await pilot.pause()
        assert isinstance(app.screen, MainScreen)

        from textual.widgets import ListView
        view = app.screen.query_one('#list-view', ListView)
        names = [item.name for item in view.children if hasattr(item, 'name')]
        assert names == ['Account', 'Bill']


# --- 4. Filter and mode switching ---------------------------------------


@pytest.mark.asyncio
async def test_main_screen_filter_narrows_list():
    app = _make_app(services=['Account', 'Bill', 'Customer'], models=['Address'])
    async with app.run_test() as pilot:
        await pilot.click('#use-env')
        for _ in range(20):
            if isinstance(app.screen, MainScreen):
                break
            await pilot.pause()
        assert isinstance(app.screen, MainScreen)

        from textual.widgets import Input, ListView
        app.screen.query_one('#filter-input', Input).value = 'cus'
        await pilot.pause()
        view = app.screen.query_one('#list-view', ListView)
        names = [item.name for item in view.children if hasattr(item, 'name')]
        assert names == ['Customer']


@pytest.mark.asyncio
async def test_call_binding_active_on_every_tab():
    """The Enter/Call footer hint is always available - on Services and
    Inquiries it opens a call screen, on Models it opens the model
    builder."""
    app = _make_app(services=['Account'], models=['Address', 'Person'])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        screen = app.screen
        from textual.widgets import Button

        assert screen.check_action('invoke_selected', ()) is True

        screen.query_one('#tab-models', Button).press()
        await pilot.pause()
        assert screen.check_action('invoke_selected', ()) is True

        screen.query_one('#tab-services', Button).press()
        await pilot.pause()
        assert screen.check_action('invoke_selected', ()) is True


@pytest.mark.asyncio
async def test_main_screen_switches_to_models_tab():
    app = _make_app(services=['Bill'], models=['Address', 'Person'])
    async with app.run_test() as pilot:
        await pilot.click('#use-env')
        for _ in range(20):
            if isinstance(app.screen, MainScreen):
                break
            await pilot.pause()
        assert isinstance(app.screen, MainScreen)

        from textual.widgets import Button, ListView
        app.screen.query_one('#tab-models', Button).press()
        await pilot.pause()

        view = app.screen.query_one('#list-view', ListView)
        names = [item.name for item in view.children if hasattr(item, 'name')]
        assert names == ['Address', 'Person']


# --- 5. CLI shim --------------------------------------------------------


# --- 6. Service call screen (GET methods) ------------------------------


async def _goto_main_screen(pilot, app: AcumaticaTUI) -> None:
    await pilot.click('#use-env')
    for _ in range(20):
        if isinstance(app.screen, MainScreen):
            break
        await pilot.pause()
    assert isinstance(app.screen, MainScreen)


async def _wait_for_screen(
    pilot, app: AcumaticaTUI, screen_cls, probe: str = None
) -> None:
    """Wait for `app.screen` to be `screen_cls`; optionally wait for a
    named widget to exist too (so DOM queries in the test don't race compose)."""
    for _ in range(30):
        if isinstance(app.screen, screen_cls):
            if probe is None:
                return
            try:
                app.screen.query_one(probe)
                return
            except Exception:
                pass
        await pilot.pause()
    raise AssertionError(f'Did not reach {screen_cls.__name__} (probe={probe})')


async def _wait_for_result(pilot, pane) -> None:
    """Poll until the result pane is no longer the loading placeholder."""
    for _ in range(30):
        rendered = str(pane.render())
        if rendered and rendered != '...':  # '...'
            return
        await pilot.pause()


async def _wait_for_widget(pilot, parent, selector: str) -> None:
    """Poll until a widget matching the selector exists below `parent`."""
    for _ in range(30):
        try:
            parent.query_one(selector)
            return
        except Exception:
            await pilot.pause()
    raise AssertionError(f'Widget {selector} did not mount')


@pytest.mark.asyncio
async def test_enter_on_service_opens_call_screen():
    app = _make_app(services=['Account', 'Bill'], models=['Address'])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from textual.widgets import ListView
        view = app.screen.query_one('#list-view', ListView)
        view.index = 0  # highlight first item (Account)
        await pilot.pause()

        # Trigger the Enter action directly (avoids focus-shift flakiness).
        app.screen.action_invoke_selected()
        await pilot.pause()

        from easy_acumatica.tui.service_call import ServiceCallScreen
        await _wait_for_screen(pilot, app, ServiceCallScreen)
        assert app.screen._service_name == 'Account'


@pytest.mark.asyncio
async def test_get_list_invokes_service_with_query_options():
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        # Wait until _post_mount_setup has finished populating the radio set -
        # the first radio button is the reliable signal that setup is done.
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        from textual.widgets import Button, Input, Static
        app.screen.query_one('#opt-top', Input).value = '5'
        app.screen.query_one('#opt-filter', Input).value = "Name eq 'foo'"

        app.screen.action_execute()
        await _wait_for_result(pilot, app.screen.query_one('#result-pane', Static))

        service = app.client._service_instances['Account']
        assert len(service.calls) == 1
        method, args, kwargs = service.calls[0]
        assert method == 'get_list'
        assert args == ()
        options = kwargs['options']
        assert options.top == 5
        assert options.filter == "Name eq 'foo'"

        rendered = str(app.screen.query_one('#result-pane', Static).render())
        assert '"Alpha"' in rendered  # the fake returned Alpha/Beta


@pytest.mark.asyncio
async def test_get_by_id_requires_entity_id():
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        screen._select_method('get_by_id')
        await _wait_for_widget(pilot, screen, '#p-entity-id')

        from textual.widgets import Button, Static
        # Execute with empty ID -> validation error, no call made
        screen.action_execute()
        await pilot.pause()

        service = app.client._service_instances['Account']
        assert service.calls == []
        status = str(screen.query_one('#call-status', Static).render())
        assert 'Entity ID is required' in status


@pytest.mark.asyncio
async def test_get_by_id_invokes_with_entity_id_only():
    """get_by_id takes just the entity id - no options kwarg (single record)."""
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        screen._method_name = 'get_by_id'
        screen._render_method_params()
        await _wait_for_widget(pilot, screen, '#p-entity-id')

        from textual.widgets import Input, Static
        screen.query_one('#p-entity-id', Input).value = 'CUST001'

        screen.action_execute()
        await _wait_for_result(pilot, screen.query_one('#result-pane', Static))

        service = app.client._service_instances['Account']
        method, args, kwargs = service.calls[0]
        assert method == 'get_by_id'
        assert args == ('CUST001',)
        assert kwargs == {}  # no options should be passed for single-record fetches


@pytest.mark.asyncio
async def test_options_hidden_for_single_record_and_schema_methods():
    """Only get_list shows the Query Options section."""
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        from textual.containers import Container
        grid = screen.query_one('#options-grid', Container)

        # Default is get_list -> options visible
        assert grid.display is True

        # Each non-get_list method hides the section
        for method in ('get_by_id', 'get_by_keys', 'get_ad_hoc_schema'):
            screen._method_name = method
            screen._sync_options_visibility()
            assert grid.display is False, f'options should be hidden for {method}'

        # Back to get_list -> visible again
        screen._method_name = 'get_list'
        screen._sync_options_visibility()
        assert grid.display is True


@pytest.mark.asyncio
async def test_method_buttons_toggle_active_class_on_click():
    """Clicking a method button switches selection and the `active` class moves."""
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        from textual.widgets import Button

        # Initially, get_list is active.
        assert screen._method_name == 'get_list'
        assert 'active' in screen.query_one('#m-get_list', Button).classes
        assert 'active' not in screen.query_one('#m-get_by_id', Button).classes

        # Switch to get_by_id.
        screen._select_method('get_by_id')
        assert screen._method_name == 'get_by_id'
        assert 'active' not in screen.query_one('#m-get_list', Button).classes
        assert 'active' in screen.query_one('#m-get_by_id', Button).classes

        # Switch back to get_list - user's reported bug was this didn't work.
        screen._select_method('get_list')
        assert screen._method_name == 'get_list'
        assert 'active' in screen.query_one('#m-get_list', Button).classes
        assert 'active' not in screen.query_one('#m-get_by_id', Button).classes


@pytest.mark.asyncio
async def test_method_selector_hides_unavailable_methods():
    """A service without get_ad_hoc_schema should not offer it."""
    client = _FakeClient(services=['Account'], models=[])
    client._service_instances['Account'].get_ad_hoc_schema = None  # not callable

    app = AcumaticaTUI(client_factory=lambda source, creds: client)

    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        # #m-get_list appears only after _post_mount_setup mounts the button row.
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        button_ids = {
            b.id for b in app.screen.query('#method-set Button') if b.id
        }

        assert 'm-get_list' in button_ids
        assert 'm-get_by_id' in button_ids
        assert 'm-get_by_keys' in button_ids
        assert 'm-get_ad_hoc_schema' not in button_ids


@pytest.mark.asyncio
async def test_get_ad_hoc_schema_invokes_with_no_params():
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        screen._method_name = 'get_ad_hoc_schema'
        screen._render_method_params()
        screen._sync_options_visibility()
        await pilot.pause()

        from textual.widgets import Static
        screen.action_execute()
        await _wait_for_result(pilot, screen.query_one('#result-pane', Static))

        service = app.client._service_instances['Account']
        assert service.calls == [('get_ad_hoc_schema', (), {})]


@pytest.mark.asyncio
async def test_get_files_invokes_with_entity_id():
    """get_files mirrors get_by_id: one entity_id positional, no options."""
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        screen._select_method('get_files')
        await _wait_for_widget(pilot, screen, '#p-entity-id')

        from textual.widgets import Input, Static
        screen.query_one('#p-entity-id', Input).value = 'CUST001'

        screen.action_execute()
        await _wait_for_result(pilot, screen.query_one('#result-pane', Static))

        service = app.client._service_instances['Account']
        method, args, kwargs = service.calls[0]
        assert method == 'get_files'
        assert args == ('CUST001',)
        assert kwargs == {}

        rendered = str(screen.query_one('#result-pane', Static).render())
        assert 'attachment.pdf' in rendered


@pytest.mark.asyncio
async def test_delete_by_id_requires_two_execute_presses():
    """Destructive methods show a warning on first press, execute on second."""
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        screen._select_method('delete_by_id')
        await _wait_for_widget(pilot, screen, '#p-entity-id')

        from textual.widgets import Input, Static
        screen.query_one('#p-entity-id', Input).value = 'CUST001'

        # First press: warning, no call made.
        screen.action_execute()
        await pilot.pause()
        status = str(screen.query_one('#call-status', Static).render())
        assert 'DESTRUCTIVE' in status
        assert 'confirm' in status.lower()
        service = app.client._service_instances['Account']
        assert service.calls == []

        # Second press: execute.
        screen.action_execute()
        await _wait_for_result(pilot, screen.query_one('#result-pane', Static))

        method, args, kwargs = service.calls[0]
        assert method == 'delete_by_id'
        assert args == ('CUST001',)
        assert kwargs == {}


@pytest.mark.asyncio
async def test_switching_method_resets_destructive_confirmation():
    """Switching methods between the two Execute presses clears the confirm flag."""
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        screen._select_method('delete_by_id')
        await _wait_for_widget(pilot, screen, '#p-entity-id')

        from textual.widgets import Input
        screen.query_one('#p-entity-id', Input).value = 'CUST001'

        # Press once -> warned.
        screen.action_execute()
        assert screen._confirmed_destructive is True

        # Switch method -> confirmation reset.
        screen._select_method('get_by_id')
        assert screen._confirmed_destructive is False

        # Switch back and press once -> warned again (didn't auto-execute).
        screen._select_method('delete_by_id')
        await _wait_for_widget(pilot, screen, '#p-entity-id')
        screen.query_one('#p-entity-id', Input).value = 'CUST001'
        screen.action_execute()

        service = app.client._service_instances['Account']
        assert service.calls == []  # no call made - still warning


@pytest.mark.asyncio
async def test_delete_by_keys_invokes_after_confirmation():
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        screen._select_method('delete_by_keys')
        await _wait_for_widget(pilot, screen, '#k-name-0')

        from textual.widgets import Input, Static
        screen.query_one('#k-name-0', Input).value = 'OrderType'
        screen.query_one('#k-value-0', Input).value = 'SO'

        # Two presses to confirm.
        screen.action_execute()
        await pilot.pause()
        screen.action_execute()
        await _wait_for_result(pilot, screen.query_one('#result-pane', Static))

        service = app.client._service_instances['Account']
        method, args, kwargs = service.calls[0]
        assert method == 'delete_by_keys'
        assert args == ()
        assert kwargs == {'OrderType': 'SO'}


@pytest.mark.asyncio
async def test_service_call_error_does_not_crash_app():
    """A raised exception in the service call surfaces in the result pane,
    not as a TUI crash. Regression: the worker used to have exit_on_error=True
    by default so any HTTP failure (bad $filter -> 500) tore the app down."""

    class _BoomService(_FakeService):
        def get_list(self, *args, **kwargs):
            self.calls.append(('get_list', args, kwargs))
            raise RuntimeError('simulated 500 from server')

    client = _FakeClient(services=['Account'], models=[])
    client._service_instances['Account'] = _BoomService('Account')
    app = AcumaticaTUI(client_factory=lambda source, creds: client)

    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        from textual.widgets import Static
        screen = app.screen
        screen.action_execute()

        # Poll until the result pane shows the error (worker completes).
        pane = screen.query_one('#result-pane', Static)
        for _ in range(30):
            rendered = str(pane.render())
            if 'RuntimeError' in rendered:
                break
            await pilot.pause()

        # App is still alive, and we're still on the call screen.
        assert isinstance(app.screen, ServiceCallScreen)

        # The error is visible in both the status bar and the result pane.
        status = str(screen.query_one('#call-status', Static).render())
        assert 'RuntimeError' in status
        assert 'simulated 500' in status

        rendered = str(pane.render())
        assert 'RuntimeError' in rendered
        assert 'simulated 500' in rendered


# --- 8. Code preview + copy + put_* methods ---------------------------------


@pytest.mark.asyncio
async def test_code_preview_shows_get_list_call_with_options():
    """The code-preview pane updates as the user fills query options."""
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        from textual.widgets import Input, Static
        screen.query_one('#opt-top', Input).value = '5'
        screen.query_one('#opt-filter', Input).value = "Status eq 'Active'"
        screen._render_preview()  # synchronous; on_input_changed would also
        await pilot.pause()

        preview = str(screen.query_one('#code-preview', Static).render())
        assert 'client.account.get_list' in preview
        assert 'top=5' in preview
        assert "Status eq 'Active'" in preview


@pytest.mark.asyncio
async def test_copy_code_button_invokes_clipboard():
    """Pressing Copy code calls App.copy_to_clipboard with the rendered text."""
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        captured: List[str] = []
        # Patch the App-level method that the screen calls.
        with patch.object(type(app), 'copy_to_clipboard',
                          lambda self, text: captured.append(text)):
            screen._copy_preview()

        assert captured, 'copy_to_clipboard was not called'
        assert 'client.account.get_list' in captured[0]


@pytest.mark.asyncio
async def test_put_file_invokes_with_bytes_from_disk(tmp_path):
    """put_file reads the local file and passes its bytes to the service."""
    app = _make_app(services=['Account'], models=[])
    test_file = tmp_path / 'attachment.txt'
    test_file.write_bytes(b'hello world')

    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        screen._select_method('put_file')
        await _wait_for_widget(pilot, screen, '#p-file-path')

        from textual.widgets import Input, Static
        screen.query_one('#p-entity-id', Input).value = 'a38c9560-913d-f111-8431-126ad4ca5ceb'
        screen.query_one('#p-file-path', Input).value = str(test_file)
        screen.query_one('#p-comment', Input).value = 'cover sheet'

        screen.action_execute()
        await _wait_for_result(pilot, screen.query_one('#result-pane', Static))

        service = app.client._service_instances['Account']
        method, args, kwargs = service.calls[0]
        assert method == 'put_file'
        # Positional: entity_id, filename, bytes
        assert args[0] == 'a38c9560-913d-f111-8431-126ad4ca5ceb'
        assert args[1] == 'attachment.txt'  # defaulted to basename
        assert args[2] == b'hello world'
        assert kwargs == {'comment': 'cover sheet'}


@pytest.mark.asyncio
async def test_put_entity_disabled_when_no_model_class_found():
    """If the service's entity has no matching model class, the Build
    button is disabled — we don't crash, we just degrade."""
    app = _make_app(services=['Account'], models=[])
    # NO client.models assignment - looking up 'Account' returns None.

    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        screen._select_method('put_entity')
        await _wait_for_widget(pilot, screen, '#build-entity')

        from textual.widgets import Button
        button = screen.query_one('#build-entity', Button)
        assert button.disabled is True


@pytest.mark.asyncio
async def test_put_entity_with_built_model_calls_service():
    """Build a flat dataclass via the model builder and execute put_entity."""
    from dataclasses import dataclass
    from typing import Optional
    from types import SimpleNamespace
    from easy_acumatica.core import BaseDataClassModel

    @dataclass
    class Account(BaseDataClassModel):
        AccountCD: Optional[str] = None
        Description: Optional[str] = None

    app = _make_app(services=['Account'], models=[])

    async with app.run_test(size=(140, 60)) as pilot:
        await _goto_main_screen(pilot, app)
        # Wire up client.models so _resolve_entity_model_class finds it.
        # Must happen AFTER the client init worker has populated app.client.
        app.client.models = SimpleNamespace(Account=Account)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        # Skip the modal builder UI and inject a built entity directly -
        # the flat-model builder is tested separately via codegen tests.
        screen._select_method('put_entity')
        await _wait_for_widget(pilot, screen, '#build-entity')
        screen._built_entity = Account(AccountCD='10000', Description='Cash')

        screen.action_execute()
        from textual.widgets import Static
        await _wait_for_result(pilot, screen.query_one('#result-pane', Static))

        service = app.client._service_instances['Account']
        method, args, kwargs = service.calls[0]
        assert method == 'put_entity'
        assert isinstance(args[0], Account)
        assert args[0].AccountCD == '10000'
        assert args[0].Description == 'Cash'
        assert kwargs == {}


@pytest.mark.asyncio
async def test_code_preview_for_put_entity_shows_construction():
    """When put_entity is configured, the preview includes the model
    construction lines and the put_entity call."""
    from dataclasses import dataclass
    from typing import Optional
    from types import SimpleNamespace
    from easy_acumatica.core import BaseDataClassModel

    @dataclass
    class Account(BaseDataClassModel):
        AccountCD: Optional[str] = None
        Description: Optional[str] = None

    app = _make_app(services=['Account'], models=[])

    async with app.run_test(size=(140, 60)) as pilot:
        await _goto_main_screen(pilot, app)
        app.client.models = SimpleNamespace(Account=Account)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        screen = app.screen
        screen._select_method('put_entity')
        await _wait_for_widget(pilot, screen, '#build-entity')
        screen._built_entity = Account(AccountCD='10000', Description='Cash')
        screen._render_preview()
        await pilot.pause()

        from textual.widgets import Static
        preview = str(screen.query_one('#code-preview', Static).render())
        assert 'AccountCD=' in preview
        assert "'10000'" in preview
        assert 'put_entity(account)' in preview
        assert 'from easy_acumatica.models import Account' in preview


def test_model_builder_coerce_helpers():
    """Quick unit-level coverage of the primitive coercion."""
    from easy_acumatica.tui.model_builder import _coerce_primitive, _split_csv

    assert _coerce_primitive('5', int) == 5
    assert _coerce_primitive('1.5', float) == 1.5
    assert _coerce_primitive('TRUE', bool) is True
    assert _coerce_primitive('no', bool) is False
    assert _coerce_primitive('', int) is None
    assert _split_csv('a, b , c', str) == ['a', 'b', 'c']
    assert _split_csv('1,2,3', int) == [1, 2, 3]
    assert _split_csv('  ', str) is None


@pytest.mark.asyncio
async def test_call_screen_back_returns_to_main():
    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Account'))
        # Wait until _post_mount_setup has finished populating the radio set -
        # the first radio button is the reliable signal that setup is done.
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#m-get_list')

        from textual.widgets import Button
        app.screen.query_one('#back', Button).press()
        await pilot.pause()

        assert isinstance(app.screen, MainScreen)


def test_build_query_options_empty_returns_none():
    """Unit-level: an all-empty form yields QueryOptions=None (so we pass nothing)."""
    from easy_acumatica.tui.service_call import _build_query_options

    form = {key: '' for key, _, _ in
            (('top', 0, 0), ('skip', 0, 0), ('select', 0, 0),
             ('expand', 0, 0), ('orderby', 0, 0), ('filter', 0, 0))}
    assert _build_query_options(form) is None


def test_build_query_options_parses_lists_and_ints():
    from easy_acumatica.tui.service_call import _build_query_options

    options = _build_query_options({
        'top': '10',
        'skip': '',
        'select': 'Name, Email',
        'expand': 'Details',
        'orderby': 'Name desc',
        'filter': "Status eq 'Active'",
    })
    assert options is not None
    assert options.top == 10
    assert options.skip is None
    assert options.select == ['Name', 'Email']
    assert options.expand == ['Details']
    assert options.orderby == 'Name desc'
    assert options.filter == "Status eq 'Active'"


def test_filter_python_F_expression_builds_filter_object():
    """Input using F-syntax returns a Filter object that renders to OData."""
    from easy_acumatica.tui.service_call import _parse_filter
    from easy_acumatica.odata import Filter

    result = _parse_filter("F.Name == 'foo'")
    assert isinstance(result, Filter)
    assert str(result) == "(Name eq 'foo')"


def test_filter_complex_F_expression_builds_filter_object():
    from easy_acumatica.tui.service_call import _parse_filter
    from easy_acumatica.odata import Filter

    result = _parse_filter("(F.Status == 'Active') & (F.Amount > 50)")
    assert isinstance(result, Filter)
    # Filter should render as OData; exact form depends on the library's
    # serialization but must contain the parts.
    rendered = str(result)
    assert 'Status' in rendered and "'Active'" in rendered
    assert 'Amount' in rendered and '50' in rendered


def test_filter_raw_odata_falls_through():
    """Plain OData text isn't valid Python - parser returns it verbatim."""
    from easy_acumatica.tui.service_call import _parse_filter

    # 'eq' isn't a Python operator -> eval fails -> raw passes through.
    result = _parse_filter("Name eq 'foo'")
    assert result == "Name eq 'foo'"


def test_filter_empty_returns_none():
    from easy_acumatica.tui.service_call import _parse_filter
    assert _parse_filter('') is None
    assert _parse_filter('   ') is None


def test_filter_non_filter_python_expression_falls_through():
    """Valid Python but not a Filter (e.g. arithmetic) is treated as raw."""
    from easy_acumatica.tui.service_call import _parse_filter

    # eval returns int 3 -> not a Filter -> fall back to raw string.
    result = _parse_filter('1 + 2')
    assert result == '1 + 2'


def test_build_query_options_invalid_int_raises():
    from easy_acumatica.tui.service_call import _build_query_options

    with pytest.raises(ValueError):
        _build_query_options({
            'top': 'not-a-number', 'skip': '', 'select': '',
            'expand': '', 'orderby': '', 'filter': '',
        })


# --- 7. CLI ---------------------------------------------------------------


def test_cli_shim_runs_tui_via_run_entry_point():
    """cli.main() delegates to tui.run()."""
    from easy_acumatica import cli

    with patch('easy_acumatica.tui.run', return_value=42) as mock_run:
        rc = cli.main([])
    assert rc == 42
    mock_run.assert_called_once()


def test_cli_shim_prints_install_hint_when_textual_missing(capsys):
    """When textual isn't installed, cli.main prints a helpful hint."""
    from easy_acumatica import cli

    # Simulate textual missing by making the tui import raise.
    real_import = __builtins__['__import__'] if isinstance(__builtins__, dict) else __import__

    def fake_import(name, *args, **kwargs):
        if name == 'easy_acumatica.tui' or name.startswith('textual'):
            raise ModuleNotFoundError("No module named 'textual'", name='textual')
        return real_import(name, *args, **kwargs)

    # Also drop any cached import of easy_acumatica.tui so the guard re-runs.
    sys.modules.pop('easy_acumatica.tui', None)

    with patch('builtins.__import__', side_effect=fake_import):
        rc = cli.main([])

    captured = capsys.readouterr()
    assert rc == 1
    assert 'pip install easy_acumatica[tui]' in captured.err


# --- 7. Inquiries tab + per-inquiry execution ---------------------------


@pytest.mark.asyncio
async def test_inquiries_tab_lists_inquiries():
    """Switching to the Inquiries tab loads list_inquiries() into the sidebar."""
    app = _make_app(
        services=['Account'],
        models=['Address'],
        inquiries=['pe_all_items', 'ar_aging_report'],
    )
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from textual.widgets import Button as _Btn
        app.screen.query_one('#tab-inquiries', _Btn).press()
        await pilot.pause()

        from textual.widgets import ListView
        view = app.screen.query_one('#list-view', ListView)
        names = [item.name for item in view.children if hasattr(item, 'name')]
        assert names == ['pe_all_items', 'ar_aging_report']

        # Call binding stays active on the inquiries tab.
        assert app.screen.check_action('invoke_selected', ()) is True


@pytest.mark.asyncio
async def test_enter_on_inquiry_opens_inquiry_call_screen():
    app = _make_app(
        services=['Account'],
        models=[],
        inquiries=['pe_all_items'],
    )
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from textual.widgets import Button as _Btn
        app.screen.query_one('#tab-inquiries', _Btn).press()
        await pilot.pause()

        from textual.widgets import ListView
        view = app.screen.query_one('#list-view', ListView)
        view.index = 0
        await pilot.pause()

        app.screen.action_invoke_selected()
        await pilot.pause()

        from easy_acumatica.tui.service_call import ServiceCallScreen
        await _wait_for_screen(pilot, app, ServiceCallScreen)
        assert app.screen._is_inquiry is True
        assert app.screen._inquiry_method == 'pe_all_items'
        assert app.screen._service_name == 'Inquiries'


@pytest.mark.asyncio
async def test_inquiry_screen_shows_options_grid_and_no_method_buttons():
    app = _make_app(
        services=['Account'],
        models=[],
        inquiries=['pe_all_items'],
    )
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Inquiries', inquiry_method='pe_all_items'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#opt-top')

        from textual.containers import Container, Horizontal
        from textual.widgets import Button

        # Wait for _post_mount_setup to finish hiding the method-set row.
        method_row = app.screen.query_one('#method-set', Horizontal)
        for _ in range(30):
            if method_row.display is False:
                break
            await pilot.pause()

        # Options grid is visible.
        grid = app.screen.query_one('#options-grid', Container)
        assert grid.display is True

        # Method-set row is hidden and contains no buttons.
        assert method_row.display is False
        assert len(method_row.query(Button)) == 0


@pytest.mark.asyncio
async def test_inquiry_execution_passes_query_options():
    app = _make_app(
        services=['Account'],
        models=[],
        inquiries=['pe_all_items'],
    )
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Inquiries', inquiry_method='pe_all_items'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#opt-top')

        from textual.widgets import Input, Static
        app.screen.query_one('#opt-top', Input).value = '5'
        app.screen.query_one('#opt-filter', Input).value = "Status eq 'Active'"

        app.screen.action_execute()
        await _wait_for_result(pilot, app.screen.query_one('#result-pane', Static))

        inquiries_service = app.client._service_instances['Inquiries']
        assert len(inquiries_service.calls) == 1
        method, args, kwargs = inquiries_service.calls[0]
        assert method == 'pe_all_items'
        assert args == ()
        options = kwargs['options']
        assert options.top == 5
        assert options.filter == "Status eq 'Active'"

        rendered = str(app.screen.query_one('#result-pane', Static).render())
        assert 'pe_all_items' in rendered


@pytest.mark.asyncio
async def test_enter_on_model_opens_model_builder():
    """Enter on a model in the Models tab opens the same builder used by
    put_entity."""
    from dataclasses import dataclass
    from typing import Optional
    from types import SimpleNamespace
    from easy_acumatica.core import BaseDataClassModel

    @dataclass
    class Address(BaseDataClassModel):
        Street: Optional[str] = None
        City: Optional[str] = None

    app = _make_app(services=['Account'], models=['Address'])

    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)
        app.client.models = SimpleNamespace(Address=Address)

        from textual.widgets import Button, ListView
        app.screen.query_one('#tab-models', Button).press()
        await pilot.pause()

        # Enter binding stays active on the Models tab now.
        assert app.screen.check_action('invoke_selected', ()) is True

        view = app.screen.query_one('#list-view', ListView)
        view.index = 0
        await pilot.pause()

        app.screen.action_invoke_selected()
        await pilot.pause()

        from easy_acumatica.tui.model_builder import ModelBuilderScreen
        await _wait_for_screen(pilot, app, ModelBuilderScreen)
        assert app.screen._model_class is Address


@pytest.mark.asyncio
async def test_top_level_model_builder_has_back_and_copy_only():
    """Builder opened from the Models tab shows Back + Copy, no Save/Cancel."""
    from dataclasses import dataclass
    from typing import Optional
    from types import SimpleNamespace
    from easy_acumatica.core import BaseDataClassModel

    @dataclass
    class Address(BaseDataClassModel):
        Street: Optional[str] = None

    app = _make_app(services=['Account'], models=['Address'])
    async with app.run_test(size=(160, 50)) as pilot:
        await _goto_main_screen(pilot, app)
        app.client.models = SimpleNamespace(Address=Address)

        from textual.widgets import Button, ListView
        app.screen.query_one('#tab-models', Button).press()
        await pilot.pause()
        view = app.screen.query_one('#list-view', ListView)
        view.index = 0
        await pilot.pause()
        app.screen.action_invoke_selected()

        from easy_acumatica.tui.model_builder import ModelBuilderScreen
        await _wait_for_screen(pilot, app, ModelBuilderScreen, probe='#cancel')

        screen = app.screen
        assert screen._top_level is True
        button_ids = {b.id for b in screen.query('#builder-buttons Button')}
        assert button_ids == {'cancel', 'copy-preview'}
        # Save action is suppressed in top-level mode.
        assert screen.check_action('save', ()) is None


@pytest.mark.asyncio
async def test_nested_model_builder_keeps_save_and_cancel():
    """Builder opened from put_entity (nested) still shows Save + Cancel."""
    from dataclasses import dataclass
    from typing import Optional
    from easy_acumatica.core import BaseDataClassModel
    from easy_acumatica.tui.model_builder import ModelBuilderScreen

    @dataclass
    class Address(BaseDataClassModel):
        Street: Optional[str] = None

    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(160, 50)) as pilot:
        await _goto_main_screen(pilot, app)
        app.push_screen(ModelBuilderScreen(Address))  # default top_level=False
        await _wait_for_screen(pilot, app, ModelBuilderScreen, probe='#save')

        screen = app.screen
        assert screen._top_level is False
        button_ids = {b.id for b in screen.query('#builder-buttons Button')}
        assert button_ids == {'cancel', 'copy-preview', 'save'}


@pytest.mark.asyncio
async def test_model_builder_preserves_inputs_when_removing_list_row():
    """Adding/removing list rows must not blank primitive Inputs the user
    has already filled in (regression test for _populate_fields rebuild)."""
    from dataclasses import dataclass, field as dc_field
    from typing import List, Optional
    from easy_acumatica.core import BaseDataClassModel
    from easy_acumatica.tui.model_builder import ModelBuilderScreen

    @dataclass
    class Line(BaseDataClassModel):
        Sku: Optional[str] = None

    @dataclass
    class Order(BaseDataClassModel):
        OrderNbr: Optional[str] = None
        Lines: List[Line] = dc_field(default_factory=list)

    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(160, 50)) as pilot:
        await _goto_main_screen(pilot, app)
        # Pre-populate one list row so we have something to remove.
        app.push_screen(ModelBuilderScreen(
            Order, prefill={'Lines': [Line(Sku='A')]}
        ))
        await _wait_for_screen(pilot, app, ModelBuilderScreen, probe='#p-OrderNbr')

        from textual.widgets import Input
        screen = app.screen
        screen.query_one('#p-OrderNbr', Input).value = 'SO-1234'
        await pilot.pause()

        # Remove the existing list row - this rebuilds the form via
        # _populate_fields. The OrderNbr text must survive.
        screen._remove_list_row('Lines', 0)
        await pilot.pause()
        await pilot.pause()

        assert screen.query_one('#p-OrderNbr', Input).value == 'SO-1234'


@pytest.mark.asyncio
async def test_model_builder_filter_narrows_visible_fields():
    """Typing into the filter input should hide field rows whose name
    doesn't contain the substring (case-insensitive). Snapshot values
    must survive filtering so the live preview keeps them."""
    from dataclasses import dataclass
    from typing import Optional
    from easy_acumatica.core import BaseDataClassModel
    from easy_acumatica.tui.model_builder import ModelBuilderScreen

    @dataclass
    class Order(BaseDataClassModel):
        OrderType: Optional[str] = None
        OrderNbr: Optional[str] = None
        CustomerID: Optional[str] = None

    app = _make_app(services=['Account'], models=[])
    async with app.run_test(size=(160, 50)) as pilot:
        await _goto_main_screen(pilot, app)
        app.push_screen(ModelBuilderScreen(Order))
        await _wait_for_screen(pilot, app, ModelBuilderScreen, probe='#p-OrderType')

        from textual.widgets import Input
        screen = app.screen

        # Set a value, then filter it out of view. Snapshot should
        # carry the value through to the preview.
        screen.query_one('#p-OrderType', Input).value = 'SO'
        await pilot.pause()
        assert "OrderType='SO'" in screen._last_preview

        # Filter to fields containing "Customer" - hides OrderType + OrderNbr.
        screen.query_one('#builder-filter', Input).value = 'customer'
        await pilot.pause()
        await pilot.pause()  # _populate_fields runs after refresh

        # OrderType widget is gone from the DOM
        with pytest.raises(Exception):
            screen.query_one('#p-OrderType', Input)
        # CustomerID is still mounted
        assert screen.query_one('#p-CustomerID', Input) is not None

        # The OrderType value snapshot should still be in the preview.
        screen._render_preview()
        await pilot.pause()
        assert "OrderType='SO'" in screen._last_preview

        # Clear the filter - everything comes back.
        screen.query_one('#builder-filter', Input).value = ''
        await pilot.pause()
        await pilot.pause()
        assert screen.query_one('#p-OrderType', Input).value == 'SO'


@pytest.mark.asyncio
async def test_model_builder_live_preview_updates_on_input():
    """Editing a primitive field updates the live code preview pane."""
    from dataclasses import dataclass
    from typing import Optional
    from easy_acumatica.core import BaseDataClassModel
    from easy_acumatica.tui.model_builder import ModelBuilderScreen

    @dataclass
    class Address(BaseDataClassModel):
        Street: Optional[str] = None
        City: Optional[str] = None

    app = _make_app(services=['Account'], models=['Address'])
    async with app.run_test(size=(160, 50)) as pilot:
        await _goto_main_screen(pilot, app)
        app.push_screen(ModelBuilderScreen(Address))
        await _wait_for_screen(
            pilot, app, ModelBuilderScreen, probe='#p-Street'
        )

        from textual.widgets import Input, Static
        screen = app.screen
        screen.query_one('#p-Street', Input).value = '1 Main'
        screen.query_one('#p-City', Input).value = 'Town'
        await pilot.pause()

        preview = screen._last_preview
        assert 'from easy_acumatica.models import Address' in preview
        assert "Street='1 Main'" in preview
        assert "City='Town'" in preview


@pytest.mark.asyncio
async def test_inquiry_preview_uses_client_inquiries_attr():
    app = _make_app(
        services=['Account'],
        models=[],
        inquiries=['pe_all_items'],
    )
    async with app.run_test(size=(140, 50)) as pilot:
        await _goto_main_screen(pilot, app)

        from easy_acumatica.tui.service_call import ServiceCallScreen
        app.push_screen(ServiceCallScreen('Inquiries', inquiry_method='pe_all_items'))
        await _wait_for_screen(pilot, app, ServiceCallScreen, probe='#opt-top')

        from textual.widgets import Input
        app.screen.query_one('#opt-top', Input).value = '3'
        # Trigger a re-render of the preview.
        app.screen._render_preview()
        await pilot.pause()

        preview = app.screen._last_preview
        assert 'client.inquiries.pe_all_items(' in preview
        assert 'options=QueryOptions' in preview
