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
    ...

@dataclass
class FileLink(BaseDataClassModel):
    comment: Optional[str] = ...
    filename: Optional[str] = ...
    href: Optional[str] = ...
    id: Optional[str] = ...

@dataclass
class TestAction(BaseDataClassModel):
    entity: 'TestModel' = ...
    parameters: Optional[Any] = ...

@dataclass
class TestModel(BaseDataClassModel):
    IsActive: Optional[bool] = ...
    Name: Optional[str] = ...
    Value: Optional[str] = ...
    files: Optional[List[Optional['FileLink']]] = ...
    id: Optional[str] = ...
"""

EXPECTED_CLIENT_PYI = """
from __future__ import annotations
from typing import Any, Union, List
from .core import BaseService, BaseDataClassModel
from .odata import QueryOptions
from . import models


class TestService(BaseService):
    def delete_by_id(self, entity_id: Union[str, List[str]], api_version: str | None = None) -> None: ...
    def get_ad_hoc_schema(self, api_version: str | None = None) -> Any: ...
    def get_by_id(self, entity_id: Union[str, List[str]], options: QueryOptions | None = None, api_version: str | None = None) -> Any: ...
    def get_list(self, options: QueryOptions | None = None, api_version: str | None = None) -> Any: ...
    def invoke_action_test_action(self, invocation: models.TestAction, api_version: str | None = None) -> Any: ...
    def put_entity(self, data: Union[dict, models.TestModel], options: QueryOptions | None = None, api_version: str | None = None) -> Any: ...
    def put_file(self, entity_id: str, filename: str, data: bytes, comment: str | None = None, api_version: str | None = None) -> None: ...

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