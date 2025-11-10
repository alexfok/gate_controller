"""BLE token scanner for detecting registered devices and iBeacons."""

import asyncio
import math
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
        self._scan_lock = asyncio.Lock()  # Prevent concurrent scans

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
        
        # Acquire lock to prevent concurrent scans
        async with self._scan_lock:
            detected = []
            detected_uuids = set()
            
            def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
                """Callback for each detected device."""
                # Check if it's an iBeacon with registered UUID
                beacon_data = self._parse_ibeacon(advertisement_data)
                if beacon_data:
                    beacon_uuid = beacon_data['uuid'].lower()
                    if beacon_uuid in self.registered_tokens and beacon_uuid not in detected_uuids:
                        detected_uuids.add(beacon_uuid)
                        token_name = self.registered_tokens[beacon_uuid]
                        rssi = getattr(device, 'rssi', None)
                        if rssi is None:
                            rssi = advertisement_data.rssi if hasattr(advertisement_data, 'rssi') else 0
                            if rssi == 0:
                                self.logger.warning(f"RSSI not available for {token_name} - BLE adapter may not support RSSI reporting")
                        tx_power = beacon_data.get('tx_power', -59)
                        distance = self._estimate_distance(rssi, tx_power)
                        signal_info = self._format_signal_info(rssi, distance)
                        
                        detected.append({
                            'uuid': beacon_uuid,
                            'name': token_name,
                            'address': device.address,
                            'rssi': rssi,
                            'distance': distance,
                            'tx_power': tx_power
                        })
                        self.logger.info(f"Detected iBeacon: {token_name} | {signal_info}")
                        
                        # Call callback if provided
                        if self.on_token_detected:
                            self.on_token_detected(beacon_uuid, token_name)
                
                # Also check regular device address/name
                device_id = self._get_device_identifier(device)
                if device_id in self.registered_tokens and device_id not in detected_uuids:
                    detected_uuids.add(device_id)
                    token_name = self.registered_tokens[device_id]
                    rssi = getattr(device, 'rssi', None)
                    if rssi is None:
                        rssi = advertisement_data.rssi if hasattr(advertisement_data, 'rssi') else 0
                        if rssi == 0:
                            self.logger.warning(f"RSSI not available for {token_name} - BLE adapter may not support RSSI reporting")
                    distance = self._estimate_distance(rssi)
                    signal_info = self._format_signal_info(rssi, distance)
                    
                    detected.append({
                        'uuid': device_id,
                        'name': token_name,
                        'address': device.address,
                        'rssi': rssi,
                        'distance': distance
                    })
                    self.logger.info(f"Detected token: {token_name} | {signal_info}")
                    
                    # Call callback if provided
                    if self.on_token_detected:
                        self.on_token_detected(device_id, token_name)
            
            try:
                scanner = BleakScanner(detection_callback=detection_callback)
                await scanner.start()
                await asyncio.sleep(duration)
                await scanner.stop()
                
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
    
    def _estimate_distance(self, rssi: int, tx_power: int = -59) -> float:
        """Estimate distance from RSSI using path loss model.
        
        Args:
            rssi: Received Signal Strength Indicator in dBm
            tx_power: Transmission power at 1 meter (default -59 for iBeacon)
            
        Returns:
            Estimated distance in meters
        """
        if rssi == 0:
            return -1.0  # Unknown distance
        
        # Path loss exponent (2.0 for free space, 2-4 for indoor environments)
        n = 2.0
        
        # Distance formula: d = 10 ^ ((TxPower - RSSI) / (10 * n))
        try:
            distance = math.pow(10, (tx_power - rssi) / (10 * n))
            return round(distance, 2)
        except:
            return -1.0
    
    def _format_signal_info(self, rssi: int, distance: float) -> str:
        """Format signal strength and distance for logging.
        
        Args:
            rssi: Signal strength in dBm
            distance: Estimated distance in meters
            
        Returns:
            Formatted string with signal info
        """
        # Signal quality assessment
        if rssi >= -60:
            quality = "Excellent"
        elif rssi >= -70:
            quality = "Good"
        elif rssi >= -80:
            quality = "Fair"
        elif rssi >= -90:
            quality = "Weak"
        else:
            quality = "Very Weak"
        
        if distance > 0:
            return f"RSSI: {rssi} dBm ({quality}), Distance: ~{distance}m"
        else:
            return f"RSSI: {rssi} dBm ({quality})"

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
        
        # Acquire lock to prevent concurrent scans
        async with self._scan_lock:
            # Use dictionaries to deduplicate by UUID/address
            beacons_dict = {}  # Key: UUID, Value: beacon info
            nearby_dict = {}   # Key: address, Value: device info
            
            def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
                """Callback for each detected device."""
                # Check if it's an iBeacon
                beacon_data = self._parse_ibeacon(advertisement_data)
                if beacon_data:
                    rssi = getattr(device, 'rssi', 0)
                    tx_power = beacon_data.get('tx_power', -59)
                    distance = self._estimate_distance(rssi, tx_power)
                    signal_info = self._format_signal_info(rssi, distance)
                    
                    beacon_uuid = beacon_data['uuid']
                    
                    # Only add/update if not already present or if RSSI is stronger
                    if beacon_uuid not in beacons_dict or rssi > beacons_dict[beacon_uuid]['rssi']:
                        beacons_dict[beacon_uuid] = {
                            'address': device.address,
                            'name': device.name or 'iBeacon',
                            'rssi': rssi,
                            'distance': distance,
                            'type': 'iBeacon',
                            'uuid': beacon_uuid,
                            'major': beacon_data['major'],
                            'minor': beacon_data['minor'],
                            'tx_power': tx_power
                        }
                        self.logger.debug(f"Found iBeacon: UUID={beacon_uuid}, Major={beacon_data['major']}, Minor={beacon_data['minor']} | {signal_info}")
                
                # Add regular device (deduplicate by address)
                if device.address not in nearby_dict:
                    rssi = getattr(device, 'rssi', 0)
                    distance = self._estimate_distance(rssi)
                    
                    nearby_dict[device.address] = {
                        'address': device.address,
                        'name': device.name or 'Unknown',
                        'rssi': rssi,
                        'distance': distance,
                        'type': 'device'
                    }
            
            try:
                scanner = BleakScanner(detection_callback=detection_callback)
                await scanner.start()
                await asyncio.sleep(duration)
                await scanner.stop()
                
                # Convert dictionaries to lists
                beacons = list(beacons_dict.values())
                nearby = list(nearby_dict.values())
                
                # Combine regular devices and beacons
                all_devices = beacons + nearby
                
                self.logger.info(f"Found {len(all_devices)} unique BLE devices ({len(beacons)} iBeacons, {len(nearby)} regular devices)")
                return all_devices
                
            except Exception as e:
                self.logger.error(f"Error listing nearby devices: {e}")
                return []

    def _parse_ibeacon(self, advertisement_data: AdvertisementData) -> Optional[Dict]:
        """Parse iBeacon data from advertisement.
        
        Args:
            advertisement_data: BLE advertisement data
            
        Returns:
            Dictionary with uuid, major, minor, tx_power if iBeacon, None otherwise
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
                    
                    # Extract TX power (byte 22) - signed 8-bit integer
                    tx_power = int.from_bytes(data[22:23], byteorder='big', signed=True)
                    
                    return {
                        'uuid': uuid,
                        'major': major,
                        'minor': minor,
                        'tx_power': tx_power
                    }
        except Exception as e:
            self.logger.debug(f"Error parsing iBeacon data: {e}")
        
        return None

