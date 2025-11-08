"""BLE token scanner for detecting registered devices."""

import asyncio
from typing import List, Dict, Set, Callable, Optional
from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from ..utils.logger import get_logger


class BLEScanner:
    """Scanner for detecting BLE tokens."""

    def __init__(self, registered_tokens: List[Dict[str, str]], 
                 on_token_detected: Optional[Callable[[str, str], None]] = None):
        """Initialize BLE scanner.
        
        Args:
            registered_tokens: List of registered token dicts with 'uuid' and 'name'
            on_token_detected: Optional callback when token is detected (uuid, name)
        """
        self.registered_tokens = {token['uuid'].lower(): token['name'] 
                                  for token in registered_tokens}
        self.on_token_detected = on_token_detected
        self.logger = get_logger(__name__)
        
        self._scanning = False
        self._detected_tokens: Set[str] = set()

    def update_registered_tokens(self, tokens: List[Dict[str, str]]):
        """Update the list of registered tokens.
        
        Args:
            tokens: List of registered token dicts with 'uuid' and 'name'
        """
        self.registered_tokens = {token['uuid'].lower(): token['name'] 
                                  for token in tokens}
        self.logger.info(f"Updated registered tokens: {len(self.registered_tokens)} tokens")

    async def scan_once(self, duration: float = 5.0) -> List[Dict[str, str]]:
        """Perform a single BLE scan.
        
        Args:
            duration: Scan duration in seconds
            
        Returns:
            List of detected registered tokens with uuid and name
        """
        self.logger.debug(f"Starting BLE scan for {duration}s...")
        
        try:
            # Discover devices
            devices = await BleakScanner.discover(timeout=duration)
            
            detected = []
            for device in devices:
                # Check if device is a registered token
                # We check both the address and name
                device_id = self._get_device_identifier(device)
                
                if device_id in self.registered_tokens:
                    token_name = self.registered_tokens[device_id]
                    detected.append({
                        'uuid': device_id,
                        'name': token_name,
                        'address': device.address,
                        'rssi': getattr(device, 'rssi', 0)
                    })
                    self.logger.info(f"Detected registered token: {token_name} ({device_id})")
                    
                    # Call callback if provided
                    if self.on_token_detected:
                        self.on_token_detected(device_id, token_name)
            
            if not detected:
                self.logger.debug(f"No registered tokens detected in scan")
            
            return detected
            
        except Exception as e:
            self.logger.error(f"BLE scan error: {e}")
            return []

    async def start_continuous_scan(self, interval: float = 5.0):
        """Start continuous BLE scanning.
        
        Args:
            interval: Scan interval in seconds
        """
        self._scanning = True
        self.logger.info(f"Starting continuous BLE scan (interval: {interval}s)")
        
        while self._scanning:
            detected = await self.scan_once(duration=interval)
            
            # Track newly detected tokens
            current_uuids = {token['uuid'] for token in detected}
            newly_detected = current_uuids - self._detected_tokens
            
            for uuid in newly_detected:
                name = self.registered_tokens.get(uuid, 'Unknown')
                self.logger.info(f"New token detected: {name} ({uuid})")
            
            self._detected_tokens = current_uuids
            
            # Wait before next scan
            await asyncio.sleep(interval)

    def stop_scanning(self):
        """Stop continuous scanning."""
        self._scanning = False
        self.logger.info("Stopping BLE scan")

    def _get_device_identifier(self, device: BLEDevice) -> str:
        """Get device identifier for matching.
        
        Args:
            device: BLE device
            
        Returns:
            Device identifier (address or name) in lowercase
        """
        # Try address first (most reliable)
        if device.address:
            return device.address.lower()
        
        # Fall back to name
        if device.name:
            return device.name.lower()
        
        return ""

    def is_scanning(self) -> bool:
        """Check if scanner is currently scanning.
        
        Returns:
            True if scanning, False otherwise
        """
        return self._scanning

    def get_detected_tokens(self) -> Set[str]:
        """Get currently detected token UUIDs.
        
        Returns:
            Set of detected token UUIDs
        """
        return self._detected_tokens.copy()

    async def list_nearby_devices(self, duration: float = 10.0) -> List[Dict[str, str]]:
        """List all nearby BLE devices (for token registration).
        
        Args:
            duration: Scan duration in seconds
            
        Returns:
            List of nearby devices with address, name, and rssi
        """
        self.logger.info(f"Scanning for all nearby BLE devices for {duration}s...")
        
        try:
            devices = await BleakScanner.discover(timeout=duration)
            
            nearby = []
            for device in devices:
                nearby.append({
                    'address': device.address,
                    'name': device.name or 'Unknown',
                    'rssi': getattr(device, 'rssi', 0)
                })
            
            self.logger.info(f"Found {len(nearby)} nearby BLE devices")
            return nearby
            
        except Exception as e:
            self.logger.error(f"Error listing nearby devices: {e}")
            return []

