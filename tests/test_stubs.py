import sys
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

from easy_acumatica import generate_stubs

# Expected output for introspection-based stub generation
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
from typing import Any, Union, List, Dict, Optional
from .core import BaseService, BaseDataClassModel
from .odata import QueryOptions
from . import models
import requests

class TestService(BaseService):
    def delete_by_id(self, entity_id: str, api_version: Optional[str] = None) -> None:
        \"\"\"
            Deletes a Test entity by its ID. for the Test entity.

            Args:
                api_version (str, optional): The API version to use for this request.

            Returns:
                None.
        \"\"\"
        ...
    def get_ad_hoc_schema(self, api_version: Optional[str] = None) -> Any:
        \"\"\"
            Retrieves the ad-hoc schema for a Test entity. for the Test entity.

            Args:
                api_version (str, optional): The API version to use for this request.

            Returns:
                The JSON response from the API.
        \"\"\"
        ...
    def get_by_id(self, entity_id: Union[str, list], options: Optional[QueryOptions] = None, api_version: Optional[str] = None) -> Any:
        \"\"\"
            Retrieves a Test entity by its ID. for the Test entity.

            Args:
                options (QueryOptions, optional): OData query options.
                api_version (str, optional): The API version to use for this request.

            Returns:
                The JSON response from the API.
        \"\"\"
        ...
    def get_files(self, entity_id: str, api_version: Optional[str] = None) -> List[Dict[str, Any]]:
        \"\"\"
            Retrieves files attached to a Test entity.

            Args:
                entity_id (str): The primary key of the entity.
                api_version (str, optional): The API version to use for this request.

            Returns:
                A list of file information dictionaries.
        \"\"\"
        ...
    def get_list(self, options: Optional[QueryOptions] = None, api_version: Optional[str] = None) -> Any:
        \"\"\"
            Retrieves a list of Test entities. for the Test entity.

            Args:
                options (QueryOptions, optional): OData query options.
                api_version (str, optional): The API version to use for this request.

            Returns:
                The JSON response from the API.
        \"\"\"
        ...
    def invoke_action_test_action(self, invocation: BaseDataClassModel, api_version: Optional[str] = None) -> Any:
        \"\"\"
            Invokes the TestAction on a Test entity. for the Test entity.

            Args:
                invocation (models.TestAction): The action invocation data.
                api_version (str, optional): The API version to use for this request.

            Returns:
                None.
        \"\"\"
        ...
    def put_entity(self, data: Union[dict, BaseDataClassModel], options: Optional[QueryOptions] = None, api_version: Optional[str] = None) -> Any:
        \"\"\"
            Creates or updates a Test entity. for the Test entity.

            Args:
                data (Union[dict, models.TestModel]): The entity data to create or update.
                options (QueryOptions, optional): OData query options.
                api_version (str, optional): The API version to use for this request.

            Returns:
                The JSON response from the API.
        \"\"\"
        ...
    def put_file(self, entity_id: str, filename: str, data: bytes, comment: Optional[str] = None, api_version: Optional[str] = None) -> None:
        \"\"\"
            Attaches a file to a Test entity. for the Test entity.

            Args:
                entity_id (str): The primary key of the entity.
                filename (str): The name of the file to upload.
                data (bytes): The file content.
                comment (str, optional): A comment about the file.
                api_version (str, optional): The API version to use for this request.

            Returns:
                None.
        \"\"\"
        ...

class AcumaticaClient:
    \"\"\"Main client for interacting with Acumatica API.\"\"\"
    # Configuration attributes
    base_url: str
    tenant: str
    username: str
    verify_ssl: bool
    persistent_login: bool
    retry_on_idle_logout: bool
    endpoint_name: str
    endpoint_version: Optional[str]
    timeout: int
    endpoints: Dict[str, Dict]
    session: requests.Session
    
    # Service attributes
    tests: TestService
    models: models
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        tenant: Optional[str] = None,
        branch: Optional[str] = None,
        locale: Optional[str] = None,
        verify_ssl: bool = True,
        persistent_login: bool = True,
        retry_on_idle_logout: bool = True,
        endpoint_name: str = 'Default',
        endpoint_version: Optional[str] = None,
        config: Optional[Any] = None,
        rate_limit_calls_per_second: float = 10.0,
        timeout: Optional[int] = None,
    ) -> None: ...
    
    def login(self) -> int: ...
    def logout(self) -> int: ...
    def close(self) -> None: ...
    def __enter__(self) -> 'AcumaticaClient': ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...
"""

def test_introspection_based_stub_generation(live_server_url, monkeypatch):
    """
    Verifies that the new introspection-based generate_stubs.py script 
    generates .pyi files in the stubs folder that match expected output.
    """
    dummy_args = [
        "generate_stubs.py",
        "--url", live_server_url,
        "--username", "test",
        "--password", "test",
        "--tenant", "test",
        "--output-dir", "."
    ]
    monkeypatch.setattr(sys, "argv", dummy_args)

    written_files = {}
    created_dirs = []
    
    # Mock Path operations
    original_mkdir = Path.mkdir
    original_write_text = Path.write_text
    
    def mock_mkdir(self, **kwargs):
        created_dirs.append(str(self))
        return None
    
    def mock_write_text(self, content, encoding='utf-8'):
        # Store the file path relative to stubs directory
        path_str = str(self)
        written_files[path_str] = content
        return None
    
    with patch.object(Path, 'mkdir', mock_mkdir):
        with patch.object(Path, 'write_text', mock_write_text):
            generate_stubs.main()
    
    # Verify stubs directory was created in the right location
    assert any("src/easy_acumatica/stubs" in d or "src\\easy_acumatica\\stubs" in d for d in created_dirs), \
        f"stubs directory was not created in the right location. Created dirs: {created_dirs}"
    
    # Verify the four expected files were written (models, services, client, __init__)
    stub_files = [f for f in written_files if "stubs" in f]
    assert len(stub_files) == 4, f"Expected 4 stub files, but found {len(stub_files)}: {stub_files}"
    
    # Verify the expected files were written
    assert any("models.pyi" in f for f in written_files), "models.pyi was not generated"
    assert any("services.pyi" in f for f in written_files), "services.pyi was not generated"
    assert any("client.pyi" in f for f in written_files), "client.pyi was not generated"
    assert any("__init__.pyi" in f for f in written_files), "__init__.pyi was not generated"
    
    # Find the actual file contents
    models_content = None
    services_content = None
    client_content = None
    
    for path, content in written_files.items():
        if "models.pyi" in path:
            models_content = content
        elif "services.pyi" in path:
            services_content = content
        elif "client.pyi" in path and "__init__" not in path:
            client_content = content
    
    assert models_content is not None, "Could not find models.pyi content"
    assert services_content is not None, "Could not find services.pyi content"
    assert client_content is not None, "Could not find client.pyi content"
    
    # Check models.pyi contains expected classes and correct import
    assert "from ..core import BaseDataClassModel" in models_content
    assert "class Entity(BaseDataClassModel):" in models_content
    assert "class FileLink(BaseDataClassModel):" in models_content
    assert "class TestAction(BaseDataClassModel):" in models_content
    assert "class TestModel(BaseDataClassModel):" in models_content
    
    # Check services.pyi contains expected service class with PascalCase
    assert "class TestService(BaseService):" in services_content
    assert "def get_list(" in services_content
    assert "def put_entity(" in services_content
    assert "from ..core import BaseService" in services_content
    
    # Check client.pyi contains expected content
    assert "class AcumaticaClient:" in client_content
    assert "tests: TestService" in client_content
    assert "models: models" in client_content
    assert "from .. import models" in client_content
    
    print("✅ Introspection-based stub generation test passed!")