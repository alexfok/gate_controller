"""Control4 API client for gate control."""

import sys
import os
import asyncio
import aiohttp
from typing import Optional

# Add pyControl4 to path (it's in parent directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'pyControl4'))

from pyControl4.account import C4Account
from pyControl4.director import C4Director

from ..utils.logger import get_logger


class C4Client:
    """Control4 API client for gate operations."""

    def __init__(self, ip: str, username: str, password: str, 
                 gate_device_id: int = 348,
                 open_scenario: int = 21,
                 close_scenario: int = 22,
                 notification_agent_id: int = 7):
        """Initialize C4 client.
        
        Args:
            ip: Controller IP address
            username: Control4 account username
            password: Control4 account password
            gate_device_id: Device ID for gate controller
            open_scenario: Scenario number for opening gate
            close_scenario: Scenario number for closing gate
            notification_agent_id: Push notification agent ID
        """
        self.ip = ip
        self.username = username
        self.password = password
        self.gate_device_id = gate_device_id
        self.open_scenario = open_scenario
        self.close_scenario = close_scenario
        self.notification_agent_id = notification_agent_id
        
        self.logger = get_logger(__name__)
        
        self.director: Optional[C4Director] = None
        self._session: Optional[aiohttp.ClientSession] = None

    async def connect(self, max_retries: int = 3, retry_delay: float = 2.0):
        """Establish connection to Control4 controller with retry logic.
        
        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Delay between retries in seconds
        """
        self.logger.info(f"Connecting to Control4 controller at {self.ip}")
        
        last_error = None
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt + 1}/{max_retries}...")
                    await asyncio.sleep(retry_delay)
                
                # Create session with SSL verification disabled
                connector = aiohttp.TCPConnector(ssl=False)
                self._session = aiohttp.ClientSession(connector=connector)
                
                # Authenticate (with SSL disabled for account API too)
                self.logger.debug("Authenticating with Control4 account...")
                account = C4Account(self.username, self.password, session=self._session)
                await account.getAccountBearerToken()
                
                # Get controller info
                self.logger.debug("Getting controller information...")
                controllers = await account.getAccountControllers()
                controller_name = controllers.get("controllerCommonName") or controllers.get("name")
                self.logger.info(f"Connected to controller: {controller_name}")
                
                # Get director bearer token
                self.logger.debug("Getting director bearer token...")
                director_token_info = await account.getDirectorBearerToken(controller_name)
                director_bearer_token = director_token_info["token"]
                
                # Create director
                self.director = C4Director(self.ip, director_bearer_token, self._session)
                
                self.logger.info("Successfully connected to Control4")
                return  # Success, exit retry loop
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                # Clean up session on failure
                if self._session:
                    await self._session.close()
                    self._session = None
                
                if attempt == max_retries - 1:
                    # Last attempt failed
                    self.logger.error(f"Failed to connect after {max_retries} attempts: {last_error}")
                    raise last_error

    async def disconnect(self):
        """Disconnect from Control4 controller."""
        if self._session:
            await self._session.close()
            self._session = None
        self.director = None
        self.logger.info("Disconnected from Control4")

    async def open_gate(self) -> bool:
        """Open the gate.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.director:
            self.logger.error("Not connected to Control4")
            return False
        
        try:
            self.logger.info(f"Opening gate (scenario {self.open_scenario})...")
            
            result = await self.director.sendPostRequest(
                f"/api/v1/items/{self.gate_device_id}/commands",
                "Run Scenario",
                {"Scenario": self.open_scenario}
            )
            
            self.logger.info("Gate opened successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to open gate: {e}")
            return False

    async def close_gate(self) -> bool:
        """Close the gate.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.director:
            self.logger.error("Not connected to Control4")
            return False
        
        try:
            self.logger.info(f"Closing gate (scenario {self.close_scenario})...")
            
            result = await self.director.sendPostRequest(
                f"/api/v1/items/{self.gate_device_id}/commands",
                "Run Scenario",
                {"Scenario": self.close_scenario}
            )
            
            self.logger.info("Gate closed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to close gate: {e}")
            return False

    async def send_notification(self, title: str, message: str, priority: Optional[str] = None) -> bool:
        """Send push notification (DISABLED).
        
        Args:
            title: Notification title
            message: Notification message
            priority: Optional priority (low, normal, high, critical)
            
        Returns:
            True (notifications are disabled)
        """
        # Notifications disabled - just log instead
        self.logger.info(f"Notification (disabled): {title} - {message}")
        return True

    async def check_gate_status(self) -> dict:
        """Check gate status.
        
        Returns:
            Dictionary with gate status information
        """
        if not self.director:
            self.logger.error("Not connected to Control4")
            return {"error": "Not connected"}
        
        try:
            # Get device info to check status
            device_info = await self.director.getItemInfo(self.gate_device_id)
            return {"status": "online", "info": device_info}
            
        except Exception as e:
            self.logger.error(f"Failed to check gate status: {e}")
            return {"error": str(e)}

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

