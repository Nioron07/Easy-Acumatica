# easy_acumatica/sub_services/customers.py

from __future__ import annotations

from typing import TYPE_CHECKING

from .records import RecordsService
from ..helpers import _raise_with_detail
from ..models.query_builder import QueryOptions

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["CustomersService", "FilesService"]


class FilesService:
    """
    Sub-service for managing files attached to Acumatica records.

    Provides methods to retrieve binary file contents, attach new files,
    and fetch comments for files linked to any top-level entity record.

    Usage example
    -------------
    >>> # 1) Download a file by its internal file ID
    >>> data = client.files.get_file("24.200.001", "9be45eb7-f97d-400b-96a5-1c4cf82faa96")
    >>> with open("download.jpg", "wb") as f:
    ...     f.write(data)

    >>> # 2) Attach a local file to a record
    >>> #    First, fetch the record to get its files:put template
    >>> rec = client.records.get_record_by_key_field(
    ...     "24.200.001", "StockItem", "InventoryID", "EJECTOR03"
    ... )
    >>> href_template = rec["_links"]["files:put"]
    >>> file_bytes = open("T2MCRO.jpg", "rb").read()
    >>> client.files.attach_file_to_record(
    ...     href_template, "T2MCRO.jpg", file_bytes, comment="Test comment"
    ... )

    >>> # 3) List file comments on a record
    >>> comments = client.files.get_file_comments_by_key_field(
    ...     "24.200.001", "StockItem", "InventoryID", "EJECTOR03"
    ... )
    >>> for file in comments:
    ...     print(file["filename"], file.get("comment"))
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    # ------------------------------------------------------------------
    def get_file(
        self,
        api_version: str,
        file_id: str
    ) -> bytes:
        """
        Retrieve a file attached to a record by its internal file ID.

        Sends a GET request to:
            {base_url}/entity/Default/{api_version}/files/{file_id}

        No query parameters or body are required.

        Request Headers
        ---------------
        Accept: application/octet-stream

        Returns
        -------
        bytes
            The raw bytes of the file.

        Raises
        ------
        RuntimeError
            If the HTTP response status is not 2xx, with details extracted
            from the response by `_raise_with_detail`.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = (
            f"{self._client.base_url}"
            f"/entity/Default/{api_version}/files/{file_id}"
        )
        resp = self._client._request(
            "get",
            url,
            headers={"Accept": "application/octet-stream"},
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.content

    # ------------------------------------------------------------------
    def attach_file_to_record(
        self,
        href_template: str,
        filename: str,
        content: bytes,
        comment: str | None = None
    ) -> None:
        """
        Attach a binary file to a record.

        Use the `href_template` from the record’s
        `_links["files:put"]`, which will contain a `{filename}` placeholder
        and the full API path segment, e.g.:
            "/MyInstance/entity/Default/24.200.001/files/.../{filename}"

        This method:
          1. Substitutes `{filename}` in the template.
          2. Prefixes the full base_url (preserving the instance path).
          3. Issues a PUT with:
               - Accept: application/json
               - Content-Type: application/octet-stream
               - PX-CbFileComment: <comment> (if provided)
               - Body: raw bytes

        Args
        ----
        href_template : str
            Path or full URL template containing `{filename}`.
        filename : str
            Name to substitute into the template.
        content : bytes
            Raw file bytes to upload.
        comment : str | None, optional
            Optional comment, sent via PX-CbFileComment header.

        Raises
        ------
        RuntimeError
            If the HTTP response status is not 2xx, via `_raise_with_detail`.
        """
        if not self._client.persistent_login:
            self._client.login()

        # Build and normalize URL
        url_part = href_template.format(filename=filename)
        if url_part.lower().startswith(("http://", "https://")):
            full_url = url_part
        elif url_part.startswith("/"):
            full_url = self._client.base_url.rstrip("/") + url_part
        else:
            full_url = self._client.base_url.rstrip("/") + "/" + url_part

        # Prepare headers
        headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/octet-stream",
        }
        if comment is not None:
            headers["PX-CbFileComment"] = comment

        resp = self._client._request(
            "put",
            full_url,
            headers=headers,
            data=content,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

    # ------------------------------------------------------------------
    def get_file_comments_by_key_field(
        self,
        api_version: str,
        entity: str,
        key: str,
        value: str
    ) -> list[dict]:
        """
        Retrieve attached files and their comments for a record identified
        by a key field.

        Internally calls RecordsService.get_record_by_key_field with
        $select=files and $expand=files, then returns the `files` list.

        Returns
        -------
        List[dict]
            Each dict has keys: "id", "filename", "href", and "comment".

        Raises
        ------
        RuntimeError
            On HTTP errors.
        """
        opts = QueryOptions(select=["files"], expand=["files"])
        rec = RecordsService(self._client).get_record_by_key_field(
            api_version, entity, key, value, options=opts
        )
        return rec.get("files", [])

    # ------------------------------------------------------------------
    def get_file_comments_by_id(
        self,
        api_version: str,
        entity: str,
        record_id: str
    ) -> list[dict]:
        """
        Retrieve attached files and their comments for a record identified
        by its entity ID.

        Internally calls RecordsService.get_record_by_id with
        $select=files and $expand=files, then returns the `files` list.

        Returns
        -------
        List[dict]
            Each dict has keys: "id", "filename", "href", and "comment".

        Raises
        ------
        RuntimeError
            On HTTP errors.
        """
        opts = QueryOptions(select=["files"], expand=["files"])
        rec = RecordsService(self._client).get_record_by_id(
            api_version, entity, record_id, options=opts
        )
        return rec.get("files", [])
    def delete_file(
        self,
        api_version: str,
        file_id: str
    ) -> None:
        """
        Deletes a file attachment using its unique file ID.

        Sends a DELETE request to:
            {base_url}/entity/Default/{api_version}/files/{file_id}

        Args:
            api_version: The contract API version (e.g., "24.200.001").
            file_id: The GUID of the file to be deleted.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/files/{file_id}"
        resp = self._client._request(
            "delete",
            url,
            headers={"Accept": "application/json"},
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()