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
        self.suppress_mode = True  # Default to suppressed mode
        
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
    
    def set_suppress_mode(self, enabled: bool):
        """Set suppress mode for token detection logging.
        
        Args:
            enabled: True for suppress mode (update existing entries),
                    False for extended mode (create new entries each time)
        """
        self.suppress_mode = enabled
    
    def get_suppress_mode(self) -> bool:
        """Get current suppress mode status."""
        return self.suppress_mode
    
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
        """Log token detected event with signal strength and distance.
        
        In suppress mode, updates existing entry for same token.
        In extended mode, creates new entry for each detection.
        """
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
        
        # In suppress mode, update existing entry if found
        if self.suppress_mode:
            if self._update_token_detection(token_uuid, message, details):
                return  # Entry updated, done
        
        # Extended mode or no existing entry found: add new entry
        self.add_entry("token_detected", message, details)
    
    def _update_token_detection(self, token_uuid: str, message: str, details: Dict) -> bool:
        """Update existing token detection entry if found.
        
        Args:
            token_uuid: Token UUID to find
            message: Updated message
            details: Updated details
            
        Returns:
            True if entry was found and updated, False otherwise
        """
        with self._lock:
            # Search backwards (most recent entries first) for matching token_detected entry
            for i in range(len(self.entries) - 1, -1, -1):
                entry = self.entries[i]
                if (entry.get("type") == "token_detected" and 
                    entry.get("details", {}).get("token_uuid") == token_uuid):
                    # Found existing entry - update it
                    entry["timestamp"] = datetime.now().isoformat()
                    entry["message"] = message
                    entry["details"] = details
                    entry["update_count"] = entry.get("update_count", 0) + 1
                    self._save_entries()
                    return True
            return False
    
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

