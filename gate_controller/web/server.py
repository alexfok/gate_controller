"""
Web server for gate controller dashboard.
"""
import asyncio
import json
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
            
            if not uuid or not name:
                raise HTTPException(status_code=400, detail="UUID and name required")
            
            success = self.controller.register_token(uuid, name)
            if success:
                self.activity_log.log_token_registered(uuid, name)
                await self._broadcast_update("token_registered", {"uuid": uuid, "name": name})
                return {"success": True, "message": "Token registered successfully"}
            else:
                raise HTTPException(status_code=400, detail="Token already registered")
        
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
        
        @self.app.get("/api/activity")
        async def get_activity(limit: int = 50, event_type: Optional[str] = None):
            """Get activity log entries."""
            entries = self.activity_log.get_entries(limit=limit, event_type=event_type)
            return {"entries": entries}
        
        @self.app.delete("/api/activity")
        async def clear_activity():
            """Clear activity log."""
            self.activity_log.clear_entries()
            await self._broadcast_update("activity_cleared", {})
            return {"success": True, "message": "Activity log cleared"}
        
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
                        "gate_status": self.controller.gate_state,
                        "active_session": self.controller.active_session is not None
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
    
    async def broadcast_token_detected(self, token_uuid: str, token_name: str):
        """Broadcast token detection event."""
        await self._broadcast_update("token_detected", {
            "uuid": token_uuid,
            "name": token_name
        })
    
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

