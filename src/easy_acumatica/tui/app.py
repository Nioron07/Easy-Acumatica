"""Top-level Textual app for easy_acumatica."""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from textual.app import App
from textual.worker import Worker, WorkerState

from .screens import (
    CredentialsScreen,
    ErrorModal,
    LoadingScreen,
    MainScreen,
    StartScreen,
)


ClientFactory = Callable[[str, Dict[str, str]], Any]


def _default_client_factory(source: str, credentials: Dict[str, str]) -> Any:
    """Build an AcumaticaClient from .env or from a credentials dict."""
    from easy_acumatica import AcumaticaClient

    common = dict(cache_methods=True)
    if source == 'env':
        return AcumaticaClient(**common)
    # source == 'manual'
    kwargs = {k: v for k, v in credentials.items() if v}
    kwargs.setdefault('endpoint_name', 'Default')
    # Opt out of auto-load so we don't silently mix manual creds with .env.
    kwargs['auto_load_env'] = False
    return AcumaticaClient(**common, **kwargs)


class AcumaticaTUI(App):
    """Interactive TUI for exploring an Acumatica instance."""

    CSS_PATH = 'styles.tcss'
    TITLE = 'Easy Acumatica'
    SUB_TITLE = 'debug tool'

    def __init__(
        self,
        *,
        client_factory: Optional[ClientFactory] = None,
    ) -> None:
        super().__init__()
        self.client: Any = None
        self._client_factory: ClientFactory = client_factory or _default_client_factory

    def on_mount(self) -> None:
        self.push_screen(StartScreen())

    # -- Client init orchestration ---------------------------------------

    def start_client_init(self, source: str, credentials: Dict[str, str]) -> None:
        """
        Called by LoadingScreen when it mounts. Runs the blocking client
        init on a worker thread so the UI stays responsive.
        """
        self._init_source = source
        self._init_credentials = credentials
        # Thread worker so the sync AcumaticaClient(...) call doesn't block
        # the async event loop.
        self.run_worker(
            self._build_client,
            thread=True,
            exclusive=True,
            name='client-init',
        )

    def _build_client(self) -> Any:
        return self._client_factory(self._init_source, self._init_credentials)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.name != 'client-init':
            return
        state = event.state
        if state == WorkerState.SUCCESS:
            self.client = event.worker.result
            # Replace StartScreen/CredentialsScreen + LoadingScreen with MainScreen.
            # Pop loading screen, then swap start screen for main.
            try:
                self.pop_screen()  # LoadingScreen
            except Exception:
                pass
            self.push_screen(MainScreen())
        elif state == WorkerState.ERROR:
            err = event.worker.error
            message = str(err) if err else 'Unknown error while initializing client.'
            try:
                self.pop_screen()  # LoadingScreen
            except Exception:
                pass
            # Show error on top of StartScreen / CredentialsScreen.
            self.push_screen(ErrorModal(message))

    # -- Shutdown --------------------------------------------------------

    def on_unmount(self) -> None:
        client = self.client
        self.client = None
        if client is None:
            return
        try:
            client.logout()
        except Exception:
            pass
        try:
            client.close()
        except Exception:
            pass
