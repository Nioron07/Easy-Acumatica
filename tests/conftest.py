import threading
import time

import pytest

from .mock_server import app  # Import your Flask app


@pytest.fixture(scope="session")
def live_server_url():
    """
    Starts the Flask app in a background thread and provides the server's URL
    to the tests. The `scope="session"` ensures the server is started only
    once for the entire test session.
    """
    server_host = "127.0.0.1"
    server_port = 5000
    server_url = f"http://{server_host}:{server_port}"

    # Define a function to run the Flask app
    def run_app():
        app.run(host=server_host, port=server_port)

    # Start the Flask app in a daemon thread.
    # A daemon thread will exit when the main thread (pytest) exits.
    server_thread = threading.Thread(target=run_app, daemon=True)
    server_thread.start()

    # Wait a moment for the server to be ready. A better approach for
    # production-grade tests would be to poll the server's health check
    # endpoint until it responds successfully.
    time.sleep(1) # Simple but effective for local testing

    # "yield" the server URL to the tests
    yield server_url

    # Teardown (this part is not strictly necessary with daemon threads,
    # but it's good practice to show where cleanup would go).
    # In a real-world scenario, you might add code here to gracefully
    # shut down the server if it weren't a daemon.
