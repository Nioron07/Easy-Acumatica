import requests
import json
from .exceptions import AcumaticaError # Import the new exception

# This can be removed or kept, but the new exception is more specific
# auth_error_msg = ("Acumatica API error {code}: {detail}")

def _raise_with_detail(resp: requests.Response) -> None:
    """
    Raise AcumaticaError with a readable explanation when the HTTP
    status is not 2xx.
    """
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        try:
            data = resp.json()
            if isinstance(data, dict):
                detail = (
                    data.get("exceptionMessage")
                    or data.get("message")
                    or json.dumps(data, ensure_ascii=False)
                )
            else:
                detail = str(data)
        except ValueError:
            detail = resp.text or str(resp.status_code)

        msg = f"Acumatica API error {resp.status_code}: {detail}"
        raise AcumaticaError(msg) from exc