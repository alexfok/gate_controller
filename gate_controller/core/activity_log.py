"""
Activity logging for gate controller events.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import asyncio
from threading import Lock


class ActivityLog:
    """Manages activity logging for gate controller events."""
    
    def __init__(self, log_file: str = "logs/activity.json", max_entries: int = 1000):
        """
        Initialize activity log.
        
        Args:
            log_file: Path to activity log file
            max_entries: Maximum number of entries to keep in memory
        """
        self.log_file = Path(log_file)
        self.max_entries = max_entries
        self.entries: List[Dict] = []
        self._lock = Lock()
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing entries
        self._load_entries()
    
    def _load_entries(self):
        """Load existing log entries from file."""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    self.entries = json.load(f)
                    # Keep only the most recent entries
                    if len(self.entries) > self.max_entries:
                        self.entries = self.entries[-self.max_entries:]
            except Exception as e:
                print(f"Error loading activity log: {e}")
                self.entries = []
    
    def _save_entries(self):
        """Save log entries to file."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.entries, f, indent=2)
        except Exception as e:
            print(f"Error saving activity log: {e}")
    
    def add_entry(self, event_type: str, message: str, details: Optional[Dict] = None):
        """
        Add a new log entry.
        
        Args:
            event_type: Type of event (gate_opened, gate_closed, token_detected, etc.)
            message: Human-readable message
            details: Additional event details
        """
        with self._lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "message": message,
                "details": details or {}
            }
            
            self.entries.append(entry)
            
            # Trim if exceeded max entries
            if len(self.entries) > self.max_entries:
                self.entries = self.entries[-self.max_entries:]
            
            # Save to file
            self._save_entries()
    
    def get_entries(self, limit: Optional[int] = None, event_type: Optional[str] = None) -> List[Dict]:
        """
        Get log entries.
        
        Args:
            limit: Maximum number of entries to return (most recent first)
            event_type: Filter by event type
            
        Returns:
            List of log entries
        """
        with self._lock:
            entries = self.entries.copy()
            
            # Filter by type if specified
            if event_type:
                entries = [e for e in entries if e["type"] == event_type]
            
            # Reverse to get most recent first
            entries.reverse()
            
            # Limit if specified
            if limit:
                entries = entries[:limit]
            
            return entries
    
    def clear_entries(self):
        """Clear all log entries."""
        with self._lock:
            self.entries = []
            self._save_entries()
    
    # Convenience methods for common events
    def log_gate_opened(self, reason: str, token_name: Optional[str] = None):
        """Log gate opened event."""
        details = {}
        if token_name:
            details["token_name"] = token_name
        self.add_entry("gate_opened", f"Gate opened: {reason}", details)
    
    def log_gate_closed(self, reason: str):
        """Log gate closed event."""
        self.add_entry("gate_closed", f"Gate closed: {reason}")
    
    def log_token_detected(self, token_uuid: str, token_name: str, rssi: int = None, distance: float = None):
        """Log token detected event with signal strength and distance."""
        details = {"token_uuid": token_uuid, "token_name": token_name}
        
        message_parts = [f"Token detected: {token_name}"]
        
        if rssi is not None:
            details["rssi"] = rssi
            details["signal_quality"] = self._get_signal_quality(rssi)
            message_parts.append(f"RSSI: {rssi} dBm ({details['signal_quality']})")
        
        if distance is not None and distance > 0:
            details["distance_meters"] = distance
            message_parts.append(f"Distance: ~{distance}m")
        
        message = " | ".join(message_parts)
        self.add_entry("token_detected", message, details)
    
    def _get_signal_quality(self, rssi: int) -> str:
        """Get signal quality description from RSSI."""
        if rssi >= -60:
            return "Excellent"
        elif rssi >= -70:
            return "Good"
        elif rssi >= -80:
            return "Fair"
        elif rssi >= -90:
            return "Weak"
        else:
            return "Very Weak"
    
    def log_token_registered(self, token_uuid: str, token_name: str):
        """Log token registered event."""
        self.add_entry(
            "token_registered",
            f"Token registered: {token_name}",
            {"token_uuid": token_uuid, "token_name": token_name}
        )
    
    def log_token_unregistered(self, token_uuid: str, token_name: str):
        """Log token unregistered event."""
        self.add_entry(
            "token_unregistered",
            f"Token unregistered: {token_name}",
            {"token_uuid": token_uuid, "token_name": token_name}
        )
    
    def log_error(self, message: str, details: Optional[Dict] = None):
        """Log error event."""
        self.add_entry("error", message, details)
    
    def log_info(self, message: str, details: Optional[Dict] = None):
        """Log info event."""
        self.add_entry("info", message, details)

