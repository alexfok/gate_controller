"""Tests for configuration management."""

import os
import tempfile
import pytest
from gate_controller.config.config import Config


class TestConfig:
    """Test configuration management."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.c4_ip == ''
        assert config.gate_device_id == 348
        assert config.auto_close_timeout == 300
        assert config.session_timeout == 60

    def test_load_from_file(self):
        """Test loading configuration from file."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
c4:
  ip: "192.168.1.100"
  username: "test@example.com"
  password: "testpass"
  gate_device_id: 123

gate:
  auto_close_timeout: 600
  session_timeout: 120

tokens:
  registered:
    - uuid: "AA:BB:CC:DD:EE:FF"
      name: "Test Token"
""")
            config_file = f.name
        
        try:
            config = Config(config_file)
            
            assert config.c4_ip == "192.168.1.100"
            assert config.c4_username == "test@example.com"
            assert config.gate_device_id == 123
            assert config.auto_close_timeout == 600
            assert config.session_timeout == 120
            assert len(config.registered_tokens) == 1
            assert config.registered_tokens[0]['uuid'] == "AA:BB:CC:DD:EE:FF"
        finally:
            os.unlink(config_file)

    def test_add_token(self):
        """Test adding a token."""
        config = Config()
        
        success = config.add_token("11:22:33:44:55:66", "Test Device")
        assert success is True
        
        tokens = config.registered_tokens
        assert len(tokens) == 1
        assert tokens[0]['uuid'] == "11:22:33:44:55:66"
        assert tokens[0]['name'] == "Test Device"
        
        # Try adding duplicate
        success = config.add_token("11:22:33:44:55:66", "Duplicate")
        assert success is False
        assert len(config.registered_tokens) == 1

    def test_remove_token(self):
        """Test removing a token."""
        config = Config()
        
        config.add_token("11:22:33:44:55:66", "Test Device")
        assert len(config.registered_tokens) == 1
        
        success = config.remove_token("11:22:33:44:55:66")
        assert success is True
        assert len(config.registered_tokens) == 0
        
        # Try removing non-existent
        success = config.remove_token("99:99:99:99:99:99")
        assert success is False

    def test_save_config(self):
        """Test saving configuration to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_file = f.name
        
        try:
            config = Config(config_file)
            config.add_token("AA:BB:CC:DD:EE:FF", "Test Token")
            config.save()
            
            # Load again and verify
            config2 = Config(config_file)
            assert len(config2.registered_tokens) == 1
            assert config2.registered_tokens[0]['uuid'] == "AA:BB:CC:DD:EE:FF"
        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)

