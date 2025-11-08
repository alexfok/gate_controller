"""BLE token scanner for detecting registered devices and iBeacons."""

import asyncio
from typing import List, Dict, Set, Callable, Optional
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

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
            List of nearby devices with address, name, rssi, and beacon info
        """
        self.logger.info(f"Scanning for all nearby BLE devices and iBeacons for {duration}s...")
        
        nearby = []
        beacons = []
        
        def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
            """Callback for each detected device."""
            # Check if it's an iBeacon
            beacon_data = self._parse_ibeacon(advertisement_data)
            if beacon_data:
                beacons.append({
                    'address': device.address,
                    'name': device.name or 'iBeacon',
                    'rssi': getattr(device, 'rssi', 0),
                    'type': 'iBeacon',
                    'uuid': beacon_data['uuid'],
                    'major': beacon_data['major'],
                    'minor': beacon_data['minor']
                })
                self.logger.info(f"Found iBeacon: UUID={beacon_data['uuid']}, Major={beacon_data['major']}, Minor={beacon_data['minor']}")
            
            # Add regular device
            device_key = f"{device.address}:{device.name}"
            if device_key not in [f"{d['address']}:{d['name']}" for d in nearby]:
                nearby.append({
                    'address': device.address,
                    'name': device.name or 'Unknown',
                    'rssi': getattr(device, 'rssi', 0),
                    'type': 'device'
                })
        
        try:
            scanner = BleakScanner(detection_callback=detection_callback)
            await scanner.start()
            await asyncio.sleep(duration)
            await scanner.stop()
            
            # Combine regular devices and beacons
            all_devices = beacons + nearby
            
            self.logger.info(f"Found {len(all_devices)} BLE devices ({len(beacons)} iBeacons, {len(nearby)} regular devices)")
            return all_devices
            
        except Exception as e:
            self.logger.error(f"Error listing nearby devices: {e}")
            return []

    def _parse_ibeacon(self, advertisement_data: AdvertisementData) -> Optional[Dict]:
        """Parse iBeacon data from advertisement.
        
        Args:
            advertisement_data: BLE advertisement data
            
        Returns:
            Dictionary with uuid, major, minor if iBeacon, None otherwise
        """
        try:
            # iBeacon manufacturer data for Apple (0x004C)
            if 0x004C in advertisement_data.manufacturer_data:
                data = advertisement_data.manufacturer_data[0x004C]
                
                # iBeacon format: type(1) + length(1) + uuid(16) + major(2) + minor(2) + tx_power(1)
                if len(data) >= 23 and data[0] == 0x02 and data[1] == 0x15:
                    # Extract UUID (bytes 2-18)
                    uuid_bytes = data[2:18]
                    uuid = '-'.join([
                        uuid_bytes[0:4].hex().upper(),
                        uuid_bytes[4:6].hex().upper(),
                        uuid_bytes[6:8].hex().upper(),
                        uuid_bytes[8:10].hex().upper(),
                        uuid_bytes[10:16].hex().upper()
                    ])
                    
                    # Extract major (bytes 18-20)
                    major = int.from_bytes(data[18:20], byteorder='big')
                    
                    # Extract minor (bytes 20-22)
                    minor = int.from_bytes(data[20:22], byteorder='big')
                    
                    return {
                        'uuid': uuid,
                        'major': major,
                        'minor': minor
                    }
        except Exception as e:
            self.logger.debug(f"Error parsing iBeacon data: {e}")
        
        return None

