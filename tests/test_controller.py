"""Tests for gate controller."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from gate_controller.config.config import Config
from gate_controller.core.controller import GateController, GateState


class TestGateController:
    """Test gate controller."""

    def test_initialization(self):
        """Test controller initialization."""
        config = Config()
        controller = GateController(config)
        
        assert controller.gate_state == GateState.UNKNOWN
        assert controller.last_open_time is None
        assert controller.session_start_time is None
        assert controller._running is False

    @pytest.mark.asyncio
    async def test_register_token(self):
        """Test registering a token through controller."""
        config = Config()
        controller = GateController(config)
        
        success = controller.register_token("AA:BB:CC:DD:EE:FF", "Test Device")
        
        assert success is True
        assert len(controller.get_registered_tokens()) == 1

    @pytest.mark.asyncio
    async def test_unregister_token(self):
        """Test unregistering a token through controller."""
        config = Config()
        controller = GateController(config)
        
        controller.register_token("AA:BB:CC:DD:EE:FF", "Test Device")
        success = controller.unregister_token("AA:BB:CC:DD:EE:FF")
        
        assert success is True
        assert len(controller.get_registered_tokens()) == 0

    @pytest.mark.asyncio
    async def test_open_gate(self):
        """Test opening gate."""
        config = Config()
        controller = GateController(config)
        
        # Mock C4 client
        controller.c4_client.open_gate = AsyncMock(return_value=True)
        controller.c4_client.send_notification = AsyncMock(return_value=True)
        
        success = await controller.open_gate("Test")
        
        assert success is True
        assert controller.gate_state == GateState.OPEN
        assert controller.last_open_time is not None

    @pytest.mark.asyncio
    async def test_close_gate(self):
        """Test closing gate."""
        config = Config()
        controller = GateController(config)
        
        # Mock C4 client
        controller.c4_client.close_gate = AsyncMock(return_value=True)
        controller.c4_client.send_notification = AsyncMock(return_value=True)
        
        success = await controller.close_gate("Test")
        
        assert success is True
        assert controller.gate_state == GateState.CLOSED
        assert controller.last_open_time is None
        assert controller.session_start_time is None

    @pytest.mark.asyncio
    async def test_handle_token_detected_opens_gate(self):
        """Test that detecting a token opens the gate."""
        config = Config()
        controller = GateController(config)
        
        # Mock C4 client
        controller.c4_client.open_gate = AsyncMock(return_value=True)
        controller.c4_client.send_notification = AsyncMock(return_value=True)
        
        await controller._handle_token_detected("AA:BB:CC:DD:EE:FF", "Test Device")
        
        # Should have opened gate
        assert controller.gate_state == GateState.OPEN
        assert controller.session_start_time is not None

    @pytest.mark.asyncio
    async def test_handle_token_detected_respects_session_timeout(self):
        """Test that session timeout prevents re-opening."""
        config = Config()
        config.config['gate']['session_timeout'] = 60  # 60 seconds
        controller = GateController(config)
        
        # Mock C4 client
        controller.c4_client.open_gate = AsyncMock(return_value=True)
        controller.c4_client.send_notification = AsyncMock(return_value=True)
        
        # First detection - should open
        await controller._handle_token_detected("AA:BB:CC:DD:EE:FF", "Test Device")
        first_call_count = controller.c4_client.open_gate.call_count
        
        # Second detection within timeout - should NOT open
        await controller._handle_token_detected("AA:BB:CC:DD:EE:FF", "Test Device")
        
        # Should not have called open_gate again
        assert controller.c4_client.open_gate.call_count == first_call_count

    @pytest.mark.asyncio
    async def test_check_gate_status(self):
        """Test checking gate status."""
        config = Config()
        controller = GateController(config)
        
        # Mock C4 client
        controller.c4_client.check_gate_status = AsyncMock(
            return_value={'status': 'ok'}
        )
        
        controller.gate_state = GateState.OPEN
        controller.last_open_time = datetime.now()
        
        status = await controller.check_gate_status()
        
        assert status['gate_state'] == 'open'
        assert status['last_open_time'] is not None
        assert status['c4_status']['status'] == 'ok'

    @pytest.mark.asyncio
    async def test_scanner_updates_on_token_changes(self):
        """Test that scanner is updated when tokens change."""
        config = Config()
        controller = GateController(config)
        
        initial_tokens = len(controller.ble_scanner.registered_tokens)
        
        controller.register_token("AA:BB:CC:DD:EE:FF", "Test Device")
        
        # Scanner should be updated
        assert len(controller.ble_scanner.registered_tokens) == initial_tokens + 1

