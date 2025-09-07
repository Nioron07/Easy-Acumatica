# tests/conftest.py - Simplified version that should work reliably

import pytest
import requests
import time
import threading
import socket
from contextlib import closing

# Simple Flask app import
try:
    from .mock_server import app
except ImportError:
    from mock_server import app


def find_free_port():
    """Find a free port on localhost."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


class SimpleFlaskServer:
    """Simple Flask server for testing."""
    
    def __init__(self):
        self.port = find_free_port()
        self.host = '127.0.0.1'
        self.base_url = f"http://{self.host}:{self.port}"
        self.thread = None
        self.server = None
        
    def start(self):
        """Start the server."""
        def run():
            # Suppress Flask logging
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            
            app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        
        # Wait for server to start
        self._wait_for_server()
    
    def stop(self):
        """Stop the server (Flask doesn't have a clean shutdown in this mode)."""
        # In this simple version, we rely on daemon threads
        pass
    
    def _wait_for_server(self, timeout=10):
        """Wait for server to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/entity", timeout=1)
                if response.status_code == 200:
                    return
            except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
                time.sleep(0.2)
        
        raise Exception(f"Server failed to start within {timeout} seconds")


# Global server instance
_test_server = None


@pytest.fixture(scope="session")
def live_server():
    """Start the mock server for testing."""
    global _test_server
    
    if _test_server is None:
        _test_server = SimpleFlaskServer()
        _test_server.start()
    
    yield _test_server


@pytest.fixture(scope="session")
def live_server_url(live_server):
    """Get the server URL."""
    return live_server.base_url


@pytest.fixture
def reset_server_state(live_server_url):
    """Reset server state for each test."""
    def reset():
        try:
            requests.post(f"{live_server_url}/test/cache/reset", timeout=5)
        except:
            pass
    
    reset()
    yield
    reset()


@pytest.fixture
def base_client_config(live_server_url):
    """Base config for creating test clients."""
    return {
        'base_url': live_server_url,
        'username': 'test_user',
        'password': 'test_password',
        'tenant': 'test_tenant',
        'timeout': 10
    }


@pytest.fixture
def temp_cache_dir():
    """Temporary directory for cache testing."""
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory(prefix="test_cache_") as temp_dir:
        yield Path(temp_dir)


# Suppress logging noise during tests
@pytest.fixture(autouse=True)
def suppress_logging():
    """Suppress verbose logging during tests."""
    import logging
    
    loggers = [
        logging.getLogger('easy_acumatica'),
        logging.getLogger('werkzeug'),
        logging.getLogger('requests'),
        logging.getLogger('urllib3')
    ]
    
    original_levels = [logger.level for logger in loggers]
    
    try:
        for logger in loggers:
            logger.setLevel(logging.ERROR)
        yield
    finally:
        for logger, level in zip(loggers, original_levels):
            logger.setLevel(level)