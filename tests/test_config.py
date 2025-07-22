# tests/test_config.py
"""Tests for configuration management."""

import json
import os
from pathlib import Path
import pytest
from easy_acumatica.config import AcumaticaConfig


class TestAcumaticaConfig:
    """Test the AcumaticaConfig class."""
    
    def test_from_env(self, monkeypatch):
        """Test loading config from environment variables."""
        monkeypatch.setenv("ACUMATICA_URL", "https://test.com")
        monkeypatch.setenv("ACUMATICA_USERNAME", "user")
        monkeypatch.setenv("ACUMATICA_PASSWORD", "pass")
        monkeypatch.setenv("ACUMATICA_TENANT", "tenant")
        monkeypatch.setenv("ACUMATICA_VERIFY_SSL", "false")
        
        config = AcumaticaConfig.from_env()
        
        assert config.base_url == "https://test.com"
        assert config.username == "user"
        assert config.password == "pass"
        assert config.tenant == "tenant"
        assert config.verify_ssl is False
    
    def test_from_file(self, tmp_path):
        """Test loading config from JSON file."""
        config_data = {
            "base_url": "https://test.com",
            "username": "user",
            "password": "pass",
            "tenant": "tenant",
            "branch": "MAIN"
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        config = AcumaticaConfig.from_file(config_file)
        
        assert config.base_url == "https://test.com"
        assert config.username == "user"
        assert config.branch == "MAIN"
    
    def test_to_file_excludes_password(self, tmp_path):
        """Test that saving config to file excludes password."""
        config = AcumaticaConfig(
            base_url="https://test.com",
            username="user",
            password="secret",
            tenant="tenant"
        )
        
        config_file = tmp_path / "config.json"
        config.to_file(config_file)
        
        saved_data = json.loads(config_file.read_text())
        
        assert "password" not in saved_data
        assert saved_data["username"] == "user"