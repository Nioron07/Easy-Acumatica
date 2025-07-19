import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

from easy_acumatica import generate_stubs
from tests.mock_swagger import get_swagger_json

# --- Final, Correct "Known-Good" Output ---
EXPECTED_MODELS_PYI = """
from __future__ import annotations
from typing import Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from .core import BaseDataClassModel


@dataclass
class Entity(BaseDataClassModel):
    \"\"\"
    Represents the Entity entity.

    Attributes:
        This model has no defined properties.
    \"\"\"
    ...

@dataclass
class FileLink(BaseDataClassModel):
    \"\"\"
    Represents the FileLink entity.

    Attributes:
        comment (str)
        filename (str)
        href (str)
        id (str)
    \"\"\"
    comment: Optional[str] = ...
    filename: Optional[str] = ...
    href: Optional[str] = ...
    id: Optional[str] = ...

@dataclass
class TestAction(BaseDataClassModel):
    \"\"\"
    Represents the TestAction entity.

    Attributes:
        entity (TestModel) (required)
        parameters (Any)
    \"\"\"
    entity: 'TestModel' = ...
    parameters: Optional[Any] = ...

@dataclass
class TestModel(BaseDataClassModel):
    \"\"\"
    Represents the TestModel entity.

    Attributes:
        IsActive (bool)
        Name (str)
        Value (str)
        files (List[FileLink])
        id (str)
    \"\"\"
    IsActive: Optional[bool] = ...
    Name: Optional[str] = ...
    Value: Optional[str] = ...
    files: Optional[List[Optional['FileLink']]] = ...
    id: Optional[str] = ...
"""

EXPECTED_CLIENT_PYI = """
from __future__ import annotations
from typing import Any, Union, List, Dict
from .core import BaseService, BaseDataClassModel
from .odata import QueryOptions
from . import models


class TestService(BaseService):
    def delete_by_id(self, entity_id: str, api_version: str | None = None) -> None:
        \"\"\"
            Deletes a Test entity by its ID. for the Test entity.
            
            Args:
                api_version (str, optional): The API version to use for this request.

            Returns:
                The JSON response from the API or None.
        \"\"\"
        ...
    def get_ad_hoc_schema(self, api_version: str | None = None) -> Any:
        \"\"\"
            Retrieves the ad-hoc schema for a Test entity. for the Test entity.

            Args:
                api_version (str, optional): The API version to use for this request.

            Returns:
                The JSON response from the API or None.
        \"\"\"
        ...
    def get_by_id(self, entity_id: str, options: QueryOptions | None = None, api_version: str | None = None) -> Any:
        \"\"\"
            Retrieves a Test entity by its ID. for the Test entity.

            Args:
                options (QueryOptions, optional): OData query options.
                api_version (str, optional): The API version to use for this request.

            Returns:
                The JSON response from the API or None.
        \"\"\"
        ...
    def get_list(self, options: QueryOptions | None = None, api_version: str | None = None) -> Any:
        \"\"\"
            Retrieves a list of Test entities. for the Test entity.

            Args:
                options (QueryOptions, optional): OData query options.
                api_version (str, optional): The API version to use for this request.

            Returns:
                The JSON response from the API or None.
        \"\"\"
        ...
    def invoke_action_test_action(self, invocation: models.TestAction, api_version: str | None = None) -> Any:
        \"\"\"
            Invokes the TestAction on a Test entity. for the Test entity.

            Args:
                invocation (models.TestAction): The action invocation data.
                api_version (str, optional): The API version to use for this request.

            Returns:
                The JSON response from the API or None.
        \"\"\"
        ...
    def put_entity(self, data: Union[dict, models.TestModel], options: QueryOptions | None = None, api_version: str | None = None) -> Any:
        \"\"\"
            Creates or updates a Test entity. for the Test entity.

            Args:
                data (Union[dict, models.TestModel]): The entity data to create or update.
                options (QueryOptions, optional): OData query options.
                api_version (str, optional): The API version to use for this request.

            Returns:
                The JSON response from the API or None.
        \"\"\"
        ...
    def put_file(self, entity_id: str, filename: str, data: bytes, comment: str | None = None, api_version: str | None = None) -> None:
        \"\"\"
            Attaches a file to a Test entity. for the Test entity.

            Args:
                entity_id (str): The primary key of the entity.
                filename (str): The name of the file to upload.
                data (bytes): The file content.
                comment (str, optional): A comment about the file.
                api_version (str, optional): The API version to use for this request.

            Returns:
                The JSON response from the API or None.
        \"\"\"
        ...
    def get_files(self, entity_id: str, api_version: str | None = None) -> List[Dict[str, Any]]:
        \"\"\"
            Retrieves files attached to a Test entity.

            Args:
                entity_id (str): The primary key of the entity.
                api_version (str, optional): The API version to use for this request.

            Returns:
                A list of file information dictionaries.
        \"\"\"
        ...

class AcumaticaClient:
    tests: TestService
    models: models
"""

def test_stub_generation_against_static_output(live_server_url, monkeypatch):
    """
    Verifies that the generate_stubs.py script generates .pyi files that
    exactly match a known-good, static output.
    """
    dummy_args = [
        "generate_stubs.py",
        "--url", live_server_url,
        "--username", "test",
        "--password", "test",
        "--tenant", "test",
        "--endpoint-version", "24.200.001"
    ]
    monkeypatch.setattr(sys, "argv", dummy_args)

    written_files = {}
    def mock_write_text(path_obj, content, encoding='utf-8'):
        written_files[path_obj.name] = content

    with patch.object(Path, 'write_text', mock_write_text):
        generate_stubs.main()

    assert "models.pyi" in written_files, "models.pyi was not generated."
    assert "client.pyi" in written_files, "client.pyi was not generated."

    def normalize_text(s):
        return textwrap.dedent(s).strip()

    assert normalize_text(written_files["models.pyi"]) == normalize_text(EXPECTED_MODELS_PYI)
    assert normalize_text(written_files["client.pyi"]) == normalize_text(EXPECTED_CLIENT_PYI)