"""Tests for BLE scanner."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from gate_controller.ble.scanner import BLEScanner


class TestBLEScanner:
    """Test BLE scanner."""

    def test_initialization(self):
        """Test scanner initialization."""
        tokens = [
            {'uuid': 'AA:BB:CC:DD:EE:FF', 'name': 'Device 1'},
            {'uuid': '11:22:33:44:55:66', 'name': 'Device 2'}
        ]
        
        scanner = BLEScanner(tokens)
        
        assert len(scanner.registered_tokens) == 2
        assert 'aa:bb:cc:dd:ee:ff' in scanner.registered_tokens
        assert scanner.registered_tokens['aa:bb:cc:dd:ee:ff'] == 'Device 1'

    def test_update_registered_tokens(self):
        """Test updating registered tokens."""
        scanner = BLEScanner([])
        
        tokens = [
            {'uuid': 'AA:BB:CC:DD:EE:FF', 'name': 'Device 1'}
        ]
        
        scanner.update_registered_tokens(tokens)
        
        assert len(scanner.registered_tokens) == 1
        assert 'aa:bb:cc:dd:ee:ff' in scanner.registered_tokens

    @pytest.mark.asyncio
    async def test_scan_once_no_devices(self):
        """Test scanning with no devices found."""
        scanner = BLEScanner([])
        
        with patch('gate_controller.ble.scanner.BleakScanner.discover', 
                   return_value=[]):
            detected = await scanner.scan_once(duration=1.0)
            
            assert len(detected) == 0

    @pytest.mark.asyncio
    async def test_scan_once_with_registered_device(self):
        """Test scanning with registered device."""
        tokens = [
            {'uuid': 'AA:BB:CC:DD:EE:FF', 'name': 'Test Device'}
        ]
        scanner = BLEScanner(tokens)
        
        # Mock BLE device
        mock_device = Mock()
        mock_device.address = 'AA:BB:CC:DD:EE:FF'
        mock_device.name = 'Test Device'
        mock_device.rssi = -50
        
        with patch('gate_controller.ble.scanner.BleakScanner.discover', 
                   return_value=[mock_device]):
            detected = await scanner.scan_once(duration=1.0)
            
            assert len(detected) == 1
            assert detected[0]['uuid'] == 'aa:bb:cc:dd:ee:ff'
            assert detected[0]['name'] == 'Test Device'
            assert detected[0]['rssi'] == -50

    def test_callback_on_detection(self):
        """Test callback is called when token is detected."""
        callback = Mock()
        tokens = [
            {'uuid': 'AA:BB:CC:DD:EE:FF', 'name': 'Test Device'}
        ]
        
        scanner = BLEScanner(tokens, on_token_detected=callback)
        
        # Manually trigger detection
        scanner.on_token_detected('aa:bb:cc:dd:ee:ff', 'Test Device')
        
        callback.assert_called_once_with('aa:bb:cc:dd:ee:ff', 'Test Device')

    def test_is_scanning(self):
        """Test scanning state."""
        scanner = BLEScanner([])
        
        assert scanner.is_scanning() is False
        
        scanner._scanning = True
        assert scanner.is_scanning() is True

    @pytest.mark.asyncio
    async def test_list_nearby_devices(self):
        """Test listing nearby devices."""
        scanner = BLEScanner([])
        
        # Mock BLE devices
        mock_device1 = Mock()
        mock_device1.address = 'AA:BB:CC:DD:EE:FF'
        mock_device1.name = 'Device 1'
        mock_device1.rssi = -50
        
        mock_device2 = Mock()
        mock_device2.address = '11:22:33:44:55:66'
        mock_device2.name = None  # Some devices don't have names
        mock_device2.rssi = -60
        
        with patch('gate_controller.ble.scanner.BleakScanner.discover', 
                   return_value=[mock_device1, mock_device2]):
            devices = await scanner.list_nearby_devices(duration=1.0)
            
            assert len(devices) == 2
            assert devices[0]['address'] == 'AA:BB:CC:DD:EE:FF'
            assert devices[0]['name'] == 'Device 1'
            assert devices[1]['name'] == 'Unknown'  # No name should default to 'Unknown'

