"""Tests for token manager."""

import pytest
from gate_controller.config.config import Config
from gate_controller.core.token_manager import TokenManager


class TestTokenManager:
    """Test token manager."""

    def test_register_token(self):
        """Test registering a token."""
        config = Config()
        manager = TokenManager(config)
        
        success = manager.register_token("AA:BB:CC:DD:EE:FF", "Test Device")
        assert success is True
        
        tokens = manager.get_all_tokens()
        assert len(tokens) == 1
        assert tokens[0]['uuid'] == "aa:bb:cc:dd:ee:ff"  # Should be lowercase
        assert tokens[0]['name'] == "Test Device"

    def test_register_duplicate_token(self):
        """Test registering duplicate token."""
        config = Config()
        manager = TokenManager(config)
        
        manager.register_token("AA:BB:CC:DD:EE:FF", "Device 1")
        success = manager.register_token("AA:BB:CC:DD:EE:FF", "Device 2")
        
        assert success is False
        assert len(manager.get_all_tokens()) == 1

    def test_unregister_token(self):
        """Test unregistering a token."""
        config = Config()
        manager = TokenManager(config)
        
        manager.register_token("AA:BB:CC:DD:EE:FF", "Test Device")
        success = manager.unregister_token("AA:BB:CC:DD:EE:FF")
        
        assert success is True
        assert len(manager.get_all_tokens()) == 0

    def test_unregister_nonexistent_token(self):
        """Test unregistering non-existent token."""
        config = Config()
        manager = TokenManager(config)
        
        success = manager.unregister_token("99:99:99:99:99:99")
        assert success is False

    def test_get_token_by_uuid(self):
        """Test getting token by UUID."""
        config = Config()
        manager = TokenManager(config)
        
        manager.register_token("AA:BB:CC:DD:EE:FF", "Test Device")
        
        token = manager.get_token_by_uuid("AA:BB:CC:DD:EE:FF")
        assert token is not None
        assert token['name'] == "Test Device"
        
        # Case insensitive
        token = manager.get_token_by_uuid("aa:bb:cc:dd:ee:ff")
        assert token is not None

    def test_is_token_registered(self):
        """Test checking if token is registered."""
        config = Config()
        manager = TokenManager(config)
        
        manager.register_token("AA:BB:CC:DD:EE:FF", "Test Device")
        
        assert manager.is_token_registered("AA:BB:CC:DD:EE:FF") is True
        assert manager.is_token_registered("99:99:99:99:99:99") is False

    def test_get_token_count(self):
        """Test getting token count."""
        config = Config()
        manager = TokenManager(config)
        
        assert manager.get_token_count() == 0
        
        manager.register_token("AA:BB:CC:DD:EE:FF", "Device 1")
        assert manager.get_token_count() == 1
        
        manager.register_token("11:22:33:44:55:66", "Device 2")
        assert manager.get_token_count() == 2

