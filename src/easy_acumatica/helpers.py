
import requests
import json
auth_error_msg = (
    "Acumatica API error {code}: {detail}"
)  # module‑level template keeps the f‑string in one place


def _raise_with_detail(resp: requests.Response) -> None:
    """
    Raise *RuntimeError* with a readable explanation when the HTTP
    status is not 2xx.

    * Works when the body is JSON **object**, JSON **scalar** (string,
      number, etc.), or plain text.
    * Always preserves the original `requests.HTTPError` as __cause__
      so callers can still inspect it if needed.
    """
    try:
        resp.raise_for_status()
        return  # 2xx ⇒ nothing to do
    except requests.HTTPError as exc:  # non-2xx path
        detail: str
        # ---- try to parse JSON -------------------------------------
        try:
            data = resp.json()
            if isinstance(data, dict):
                detail = (
                    data.get("exceptionMessage")
                    or data.get("message")
                    or json.dumps(data, ensure_ascii=False)
                )
            else:                          # list, str, int, …
                detail = str(data)
        except ValueError:                 # not JSON
            detail = resp.text or str(resp.status_code)

        msg = auth_error_msg.format(code=resp.status_code, detail=detail)
        raise RuntimeError(msg) from exc