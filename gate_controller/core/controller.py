"""Main gate controller with BLE token detection and automatic gate control."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from ..api.c4_client import C4Client
from ..ble.scanner import BLEScanner
from ..config.config import Config
from .token_manager import TokenManager
from ..utils.logger import get_logger

# Optional import for activity log
try:
    from .activity_log import ActivityLog
except ImportError:
    ActivityLog = None


class GateState(Enum):
    """Gate states."""
    CLOSED = "closed"
    OPENING = "opening"
    OPEN = "open"
    CLOSING = "closing"
    UNKNOWN = "unknown"


class GateController:
    """Main controller for automated gate management."""

    def __init__(self, config: Config, activity_log: Optional['ActivityLog'] = None, dashboard_server=None):
        """Initialize gate controller.
        
        Args:
            config: Configuration instance
            activity_log: Optional activity log instance for web dashboard
            dashboard_server: Optional dashboard server for WebSocket broadcasts
        """
        self.config = config
        self.logger = get_logger(__name__, config.log_level, config.log_file)
        self.activity_log = activity_log
        self.dashboard_server = dashboard_server
        
        # Initialize components
        self.c4_client = C4Client(
            ip=config.c4_ip,
            username=config.c4_username,
            password=config.c4_password,
            gate_device_id=config.gate_device_id,
            open_scenario=config.open_gate_scenario,
            close_scenario=config.close_gate_scenario,
            notification_agent_id=config.notification_agent_id
        )
        
        self.token_manager = TokenManager(config)
        
        self.ble_scanner = BLEScanner(
            registered_tokens=self.token_manager.get_all_tokens(),
            on_token_detected=self._on_token_detected
        )
        
        # State management
        self.gate_state = GateState.UNKNOWN
        self.last_open_time: Optional[datetime] = None
        self.session_start_time: Optional[datetime] = None
        self._running = False
        self._tasks = []
    
    @property
    def running(self) -> bool:
        """Check if controller is running."""
        return self._running
    
    @property
    def active_session(self) -> Optional[datetime]:
        """Get active session start time."""
        return self.session_start_time

    async def start(self):
        """Start the gate controller."""
        self.logger.info("Starting gate controller...")
        
        try:
            # Connect to Control4
            await self.c4_client.connect()
            
            # Check gate status
            await self.check_gate_status()
            
            # Start main loop
            self._running = True
            
            # Create background tasks
            self._tasks = [
                asyncio.create_task(self._ble_scan_loop()),
                asyncio.create_task(self._status_check_loop()),
                asyncio.create_task(self._auto_close_loop())
            ]
            
            self.logger.info("Gate controller started successfully")
            
            # Wait for tasks to complete (they run indefinitely)
            await asyncio.gather(*self._tasks)
            
        except Exception as e:
            self.logger.error(f"Error starting gate controller: {e}")
            raise

    async def stop(self):
        """Stop the gate controller."""
        self.logger.info("Stopping gate controller...")
        
        self._running = False
        
        # Stop BLE scanning
        self.ble_scanner.stop_scanning()
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to finish
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Disconnect from Control4
        await self.c4_client.disconnect()
        
        self.logger.info("Gate controller stopped")

    async def _ble_scan_loop(self):
        """Main loop for BLE token scanning."""
        self.logger.info("Starting BLE scan loop")
        
        while self._running:
            try:
                # Scan for tokens
                detected = await self.ble_scanner.scan_once(
                    duration=self.config.ble_scan_interval
                )
                
                if detected:
                    for token in detected:
                        await self._handle_token_detected(
                            token['uuid'], 
                            token['name'],
                            token.get('rssi'),
                            token.get('distance')
                        )
                
                # Wait before next scan
                await asyncio.sleep(self.config.ble_scan_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in BLE scan loop: {e}")
                await asyncio.sleep(self.config.ble_scan_interval)

    async def _status_check_loop(self):
        """Main loop for periodic status checks."""
        self.logger.info("Starting status check loop")
        
        while self._running:
            try:
                await self.check_gate_status()
                await asyncio.sleep(self.config.status_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in status check loop: {e}")
                await asyncio.sleep(self.config.status_check_interval)

    async def _auto_close_loop(self):
        """Main loop for automatic gate closing."""
        self.logger.info("Starting auto-close loop")
        
        while self._running:
            try:
                # Check if gate should be auto-closed
                if self.gate_state == GateState.OPEN and self.last_open_time:
                    time_open = (datetime.now() - self.last_open_time).total_seconds()
                    
                    if time_open >= self.config.auto_close_timeout:
                        self.logger.info(f"Auto-closing gate (open for {time_open}s)")
                        await self.close_gate("Auto-close timeout")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in auto-close loop: {e}")
                await asyncio.sleep(10)

    def _on_token_detected(self, uuid: str, name: str):
        """Callback when a token is detected by scanner.
        
        Args:
            uuid: Token UUID
            name: Token name
        """
        self.logger.debug(f"Token detected callback: {name} ({uuid})")

    async def _handle_token_detected(self, uuid: str, name: str, rssi: int = None, distance: float = None):
        """Handle detected token and open gate if necessary.
        
        Args:
            uuid: Token UUID
            name: Token name
            rssi: Signal strength in dBm (optional)
            distance: Estimated distance in meters (optional)
        """
        signal_info = ""
        if rssi is not None:
            signal_info = f" | RSSI: {rssi} dBm"
        if distance is not None and distance > 0:
            signal_info += f" | Distance: ~{distance}m"
        
        self.logger.info(f"Registered token detected: {name} ({uuid}){signal_info}")
        
        # Log token detection with signal strength and distance
        if self.activity_log:
            self.activity_log.log_token_detected(uuid, name, rssi, distance)
        
        # Broadcast to dashboard via WebSocket
        if self.dashboard_server:
            await self.dashboard_server.broadcast_token_detected(uuid, name, rssi, distance)
        
        # Check if token is active
        token_info = self.token_manager.get_token_by_uuid(uuid)
        if token_info:
            is_active = token_info.get('active', True)  # Default to True for backward compatibility
            if not is_active:
                self.logger.info(f"Token {name} is paused (active=False), not opening gate")
                return
        
        # Don't open if gate is already open or opening
        if self.gate_state in [GateState.OPEN, GateState.OPENING]:
            self.logger.debug(f"Gate is already {self.gate_state.value}, not opening again")
            return
        
        # Check if we're in an active session
        if self.session_start_time:
            time_since_session = (datetime.now() - self.session_start_time).total_seconds()
            
            if time_since_session < self.config.session_timeout:
                self.logger.debug(f"Still in active session ({time_since_session}s)")
                return
        
        # Start new session BEFORE opening gate to prevent race condition
        self.session_start_time = datetime.now()
        
        # Open the gate
        await self.open_gate(f"Token detected: {name}")

    async def open_gate(self, reason: str = "Manual") -> bool:
        """Open the gate.
        
        Args:
            reason: Reason for opening
            
        Returns:
            True if successful
        """
        self.logger.info(f"Opening gate - Reason: {reason}")
        
        self.gate_state = GateState.OPENING
        
        # Open via C4
        success = await self.c4_client.open_gate()
        
        if success:
            self.gate_state = GateState.OPEN
            self.last_open_time = datetime.now()
            
            # Log gate opened
            if self.activity_log:
                self.activity_log.log_gate_opened(reason)
            
            # Send notification
            await self.c4_client.send_notification(
                "Gate Opened",
                f"Gate opened: {reason}",
                priority="normal"
            )
        else:
            self.gate_state = GateState.UNKNOWN
            if self.activity_log:
                self.activity_log.log_error(f"Failed to open gate: {reason}")
        
        return success

    async def close_gate(self, reason: str = "Manual") -> bool:
        """Close the gate.
        
        Args:
            reason: Reason for closing
            
        Returns:
            True if successful
        """
        self.logger.info(f"Closing gate - Reason: {reason}")
        
        self.gate_state = GateState.CLOSING
        
        # Close via C4
        success = await self.c4_client.close_gate()
        
        if success:
            self.gate_state = GateState.CLOSED
            self.last_open_time = None
            # DON'T clear session_start_time - keep session active to prevent immediate re-opening
            # if token is still in range. Session will naturally expire after session_timeout.
            # self.session_start_time = None  # <-- This was causing the issue!
            
            # Log gate closed
            if self.activity_log:
                self.activity_log.log_gate_closed(reason)
            
            # Send notification
            await self.c4_client.send_notification(
                "Gate Closed",
                f"Gate closed: {reason}",
                priority="normal"
            )
        else:
            self.gate_state = GateState.UNKNOWN
            if self.activity_log:
                self.activity_log.log_error(f"Failed to close gate: {reason}")
        
        return success

    async def check_gate_status(self) -> dict:
        """Check current gate status.
        
        Returns:
            Status dictionary
        """
        status = await self.c4_client.check_gate_status()
        
        self.logger.debug(f"Gate status: {status}")
        
        return {
            'gate_state': self.gate_state.value,
            'last_open_time': self.last_open_time.isoformat() if self.last_open_time else None,
            'session_active': self.session_start_time is not None,
            'c4_status': status
        }

    def get_registered_tokens(self) -> list:
        """Get list of registered tokens.
        
        Returns:
            List of registered tokens
        """
        return self.token_manager.get_all_tokens()

    def register_token(self, uuid: str, name: str) -> bool:
        """Register a new token.
        
        Args:
            uuid: Token UUID
            name: Token name
            
        Returns:
            True if successful
        """
        success = self.token_manager.register_token(uuid, name)
        
        if success:
            # Update scanner with new tokens
            self.ble_scanner.update_registered_tokens(
                self.token_manager.get_all_tokens()
            )
            
            # Log token registration
            if self.activity_log:
                self.activity_log.log_token_registered(uuid, name)
        
        return success

    def unregister_token(self, uuid: str) -> bool:
        """Unregister a token.
        
        Args:
            uuid: Token UUID
            
        Returns:
            True if successful
        """
        # Get token name before unregistering (for logging)
        token = next((t for t in self.token_manager.get_all_tokens() 
                      if t['uuid'].lower() == uuid.lower()), None)
        token_name = token['name'] if token else uuid
        
        success = self.token_manager.unregister_token(uuid)
        
        if success:
            # Update scanner with new tokens
            self.ble_scanner.update_registered_tokens(
                self.token_manager.get_all_tokens()
            )
            
            # Log token unregistration
            if self.activity_log:
                self.activity_log.log_token_unregistered(uuid, token_name)
        
        return success

