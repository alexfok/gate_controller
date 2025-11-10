"""
Web server for gate controller dashboard.
"""
import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from gate_controller.config.config import Config
from gate_controller.core.controller import GateController
from gate_controller.core.activity_log import ActivityLog
from gate_controller.utils.logger import get_logger


class DashboardServer:
    """Web dashboard server for gate controller."""
    
    def __init__(self, config: Config, controller: GateController, activity_log: ActivityLog):
        """
        Initialize dashboard server.
        
        Args:
            config: Configuration object
            controller: Gate controller instance
            activity_log: Activity log instance
        """
        self.config = config
        self.controller = controller
        self.activity_log = activity_log
        self.logger = get_logger(__name__)
        
        # Create FastAPI app
        self.app = FastAPI(title="Gate Controller Dashboard")
        
        # WebSocket connections
        self.websocket_connections: List[WebSocket] = []
        
        # Setup routes
        self._setup_routes()
        
        # Setup static files and templates
        web_dir = Path(__file__).parent
        static_dir = web_dir / "static"
        templates_dir = web_dir / "templates"
        
        # Create directories if they don't exist
        static_dir.mkdir(exist_ok=True)
        templates_dir.mkdir(exist_ok=True)
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        self.templates = Jinja2Templates(directory=str(templates_dir))
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root(request: Request):
            """Serve main dashboard page."""
            return self.templates.TemplateResponse("index.html", {"request": request})
        
        @self.app.get("/api/status")
        async def get_status():
            """Get current system status."""
            return {
                "timestamp": datetime.now().isoformat(),
                "controller_running": self.controller.running,
                "gate_status": self.controller.gate_state.value if self.controller.gate_state else "unknown",
                "active_session": self.controller.active_session is not None,
                "session_start": self.controller.active_session.isoformat() if self.controller.active_session else None
            }
        
        @self.app.get("/api/tokens")
        async def get_tokens():
            """Get registered tokens."""
            tokens = self.controller.get_registered_tokens()
            return {"tokens": tokens}
        
        @self.app.post("/api/tokens")
        async def register_token(data: dict):
            """Register a new token."""
            uuid = data.get("uuid")
            name = data.get("name")
            active = data.get("active", True)  # Default to True
            
            if not uuid or not name:
                raise HTTPException(status_code=400, detail="UUID and name required")
            
            success = self.controller.register_token(uuid, name, active)
            if success:
                self.activity_log.log_token_registered(uuid, name)
                await self._broadcast_update("token_registered", {"uuid": uuid, "name": name, "active": active})
                return {"success": True, "message": "Token registered successfully"}
            else:
                raise HTTPException(status_code=400, detail="Token already registered")
        
        @self.app.patch("/api/tokens/{uuid}")
        async def update_token(uuid: str, data: dict):
            """Update a token's attributes."""
            name = data.get("name")
            active = data.get("active")
            
            if name is None and active is None:
                raise HTTPException(status_code=400, detail="At least one field (name or active) required")
            
            success = self.controller.token_manager.update_token(uuid, name=name, active=active)
            if success:
                updates = []
                if name is not None:
                    updates.append(f"name to '{name}'")
                if active is not None:
                    updates.append(f"active to {active}")
                self.activity_log.add_entry("token_updated", f"Token {uuid} updated: {', '.join(updates)}")
                await self._broadcast_update("token_updated", {"uuid": uuid, "name": name, "active": active})
                return {"success": True, "message": "Token updated successfully"}
            else:
                raise HTTPException(status_code=404, detail="Token not found")
        
        @self.app.delete("/api/tokens/{uuid}")
        async def unregister_token(uuid: str):
            """Unregister a token."""
            tokens = self.controller.get_registered_tokens()
            token = next((t for t in tokens if t["uuid"].lower() == uuid.lower()), None)
            
            if not token:
                raise HTTPException(status_code=404, detail="Token not found")
            
            success = self.controller.unregister_token(uuid)
            if success:
                self.activity_log.log_token_unregistered(uuid, token["name"])
                await self._broadcast_update("token_unregistered", {"uuid": uuid})
                return {"success": True, "message": "Token unregistered successfully"}
            else:
                raise HTTPException(status_code=400, detail="Failed to unregister token")
        
        @self.app.get("/api/scan/all")
        async def scan_all_devices(duration: int = 10):
            """Scan for all nearby BLE devices and iBeacons."""
            try:
                self.logger.info(f"Starting full BLE scan for {duration}s...")
                devices = await self.controller.ble_scanner.list_nearby_devices(duration=duration)
                
                # Separate iBeacons and regular devices
                ibeacons = [d for d in devices if d.get('type') == 'iBeacon']
                regular_devices = [d for d in devices if d.get('type') == 'device']
                
                return {
                    "success": True,
                    "ibeacons": ibeacons,
                    "devices": regular_devices,
                    "total": len(devices)
                }
            except Exception as e:
                self.logger.error(f"Failed to scan devices: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/config")
        async def get_config():
            """Get system configuration."""
            return {
                "c4": {
                    "ip": self.config.c4_ip,
                    "gate_device_id": self.config.gate_device_id,
                    "open_gate_scenario": self.config.open_gate_scenario,
                    "close_gate_scenario": self.config.close_gate_scenario
                },
                "gate": {
                    "auto_close_timeout": self.config.auto_close_timeout,
                    "session_timeout": self.config.session_timeout,
                    "status_check_interval": self.config.status_check_interval,
                    "ble_scan_interval": self.config.ble_scan_interval
                }
            }
        
        @self.app.post("/api/config")
        async def update_config(data: dict):
            """Update gate behavior configuration."""
            try:
                # Update gate configuration
                if 'auto_close_timeout' in data:
                    self.config.config['gate']['auto_close_timeout'] = int(data['auto_close_timeout'])
                if 'session_timeout' in data:
                    self.config.config['gate']['session_timeout'] = int(data['session_timeout'])
                if 'status_check_interval' in data:
                    self.config.config['gate']['status_check_interval'] = int(data['status_check_interval'])
                if 'ble_scan_interval' in data:
                    self.config.config['gate']['ble_scan_interval'] = int(data['ble_scan_interval'])
                
                # Save configuration to file
                self.config.save()
                
                self.activity_log.add_entry("config_updated", "Configuration updated via dashboard", data)
                return {"success": True, "message": "Configuration saved. Please restart the service for changes to take effect."}
            except Exception as e:
                self.logger.error(f"Failed to update configuration: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/gate/open")
        async def open_gate():
            """Manually open the gate."""
            try:
                await self.controller.c4_client.open_gate()
                self.activity_log.log_gate_opened("Manual open via dashboard")
                await self._broadcast_update("gate_opened", {"reason": "Manual"})
                return {"success": True, "message": "Gate opened"}
            except Exception as e:
                self.logger.error(f"Failed to open gate: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/gate/close")
        async def close_gate():
            """Manually close the gate."""
            try:
                await self.controller.c4_client.close_gate()
                self.activity_log.log_gate_closed("Manual close via dashboard")
                await self._broadcast_update("gate_closed", {"reason": "Manual"})
                return {"success": True, "message": "Gate closed"}
            except Exception as e:
                self.logger.error(f"Failed to close gate: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        async def _process_token_detection(uuid: str, name: str = None, rssi: int = None, distance: float = None):
            """Internal handler for token detection (shared by GET and POST)."""
            # Validate UUID
            if not uuid:
                raise HTTPException(status_code=400, detail="Token UUID is required")
            
            uuid = uuid.lower()
            
            # Check if token is registered
            token_info = self.controller.token_manager.get_token_by_uuid(uuid)
            if not token_info:
                self.logger.warning(f"Token detection ignored: {uuid} not registered")
                return {
                    "success": False,
                    "message": "Token not registered",
                    "action": "ignored"
                }
            
            name = name or token_info.get('name', 'Unknown')
            
            # Check if token is active
            is_active = token_info.get('active', True)
            if not is_active:
                self.logger.info(f"Token detection ignored: {name} is paused (active=False)")
                return {
                    "success": False,
                    "message": "Token is paused",
                    "action": "ignored"
                }
            
            # Call the same handler as BLE scanner
            self.logger.info(f"External token detected via API: {name} ({uuid})")
            await self.controller._handle_token_detected(uuid, name, rssi, distance)
            
            return {
                "success": True,
                "message": "Token detected and processed",
                "token": name,
                "action": "processed"
            }
        
        @self.app.get("/api/token/detected")
        async def token_detected_get(
            uuid: str,
            name: Optional[str] = None,
            rssi: Optional[int] = None,
            distance: Optional[float] = None
        ):
            """Handle token detection from external BLE scanner via GET (e.g., BCG04).
            
            Query parameters:
            - uuid: Token UUID (required) - e.g., 426c7565-4368-6172-6d42-6561636f6e67
            - name: Token name (optional) - e.g., BCPro_Alex
            - rssi: Signal strength in dBm (optional) - e.g., -45
            - distance: Estimated distance in meters (optional) - e.g., 0.5
            
            Example:
            GET /api/token/detected?uuid=426c7565-4368-6172-6d42-6561636f6e67&rssi=-45
            """
            try:
                return await _process_token_detection(uuid, name, rssi, distance)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to process token detection (GET): {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/token/detected")
        async def token_detected_post(data: dict):
            """Handle token detection from external BLE scanner via POST (e.g., BCG04).
            
            JSON payload:
            {
                "uuid": "426c7565-4368-6172-6d42-6561636f6e67",  // Required
                "name": "BCPro_Alex",  // Optional (will lookup from config)
                "rssi": -45,  // Optional signal strength in dBm
                "distance": 0.5  // Optional estimated distance in meters
            }
            """
            try:
                uuid = data.get('uuid')
                name = data.get('name')
                rssi = data.get('rssi')
                distance = data.get('distance')
                
                return await _process_token_detection(uuid, name, rssi, distance)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Failed to process token detection (POST): {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/activity")
        async def get_activity(limit: int = 50, event_type: Optional[str] = None):
            """Get activity log entries."""
            entries = self.activity_log.get_entries(limit=limit, event_type=event_type)
            return {"activity": entries}
        
        @self.app.delete("/api/activity")
        async def clear_activity():
            """Clear activity log."""
            self.activity_log.clear_entries()
            await self._broadcast_update("activity_cleared", {})
            return {"success": True, "message": "Activity log cleared"}
        
        @self.app.post("/api/service/restart")
        async def restart_service():
            """Restart the service if running under systemd."""
            try:
                # Check if running under systemd
                if os.environ.get('INVOCATION_ID'):
                    # Running under systemd - use systemctl to restart
                    subprocess.Popen(['sudo', 'systemctl', 'restart', 'gate-controller.service'])
                    self.activity_log.add_entry("system", "Service restart requested via dashboard")
                    return {"success": True, "message": "Service restart initiated"}
                else:
                    # Not running under systemd - can't auto-restart
                    return {
                        "success": False, 
                        "message": "Service restart not available. Please restart manually or run as systemd service."
                    }
            except Exception as e:
                self.logger.error(f"Failed to restart service: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/c4/refresh-token")
        async def refresh_c4_token():
            """Refresh C4 director token from cloud."""
            try:
                self.logger.info("Token refresh requested via dashboard...")
                
                # Call refresh_token which will trigger the callback to save
                token_info = await self.controller.c4_client.refresh_token()
                
                self.activity_log.add_entry("c4_auth", "Director token refreshed via dashboard", {
                    "controller": token_info["controller_name"]
                })
                
                return {
                    "success": True,
                    "message": "Token refreshed successfully",
                    "controller": token_info["controller_name"]
                }
            except Exception as e:
                self.logger.error(f"Failed to refresh token: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            self.logger.info(f"WebSocket client connected ({len(self.websocket_connections)} total)")
            
            try:
                # Send initial status
                await websocket.send_json({
                    "type": "status",
                    "data": {
                        "controller_running": self.controller.running,
                        "gate_status": self.controller.gate_state.value if self.controller.gate_state else "unknown",
                        "active_session": self.controller.active_session is not None,
                        "session_start": self.controller.active_session.isoformat() if self.controller.active_session else None
                    }
                })
                
                # Keep connection alive and listen for messages
                while True:
                    data = await websocket.receive_text()
                    # Handle ping/pong for keep-alive
                    if data == "ping":
                        await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
                self.logger.info(f"WebSocket client disconnected ({len(self.websocket_connections)} remaining)")
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
    
    async def _broadcast_update(self, event_type: str, data: dict):
        """Broadcast update to all connected WebSocket clients."""
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                self.logger.error(f"Failed to send to WebSocket client: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)
    
    async def broadcast_status_update(self):
        """Broadcast current status to all clients."""
        await self._broadcast_update("status", {
            "controller_running": self.controller.running,
            "gate_status": self.controller.gate_state.value if self.controller.gate_state else "unknown",
            "active_session": self.controller.active_session is not None,
            "session_start": self.controller.active_session.isoformat() if self.controller.active_session else None
        })
    
    async def broadcast_token_detected(self, token_uuid: str, token_name: str, rssi: int = None, distance: float = None):
        """Broadcast token detection event."""
        data = {
            "uuid": token_uuid,
            "name": token_name
        }
        if rssi is not None:
            data["rssi"] = rssi
        if distance is not None:
            data["distance"] = distance
        await self._broadcast_update("token_detected", data)
    
    async def broadcast_gate_opened(self, reason: str):
        """Broadcast gate opened event."""
        await self._broadcast_update("gate_opened", {"reason": reason})
    
    async def broadcast_gate_closed(self, reason: str):
        """Broadcast gate closed event."""
        await self._broadcast_update("gate_closed", {"reason": reason})
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Run the dashboard server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.logger.info(f"Starting dashboard server on http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port, log_level="info")

