"""Configuration management for gate controller."""

import os
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for gate controller."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        if config_file is None:
            config_file = self._get_default_config_path()
        
        self.config_file = config_file
        self.config = self._load_config()

    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Try multiple locations
        locations = [
            "config/config.yaml",
            "config.yaml",
            os.path.expanduser("~/.gate_controller/config.yaml"),
            "/etc/gate_controller/config.yaml"
        ]
        
        for location in locations:
            if os.path.exists(location):
                return location
        
        # Return default if none exist
        return "config/config.yaml"

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not os.path.exists(self.config_file):
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                return config or {}
        except Exception as e:
            print(f"Warning: Failed to load config from {self.config_file}: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'c4': {
                'ip': '',
                'username': '',
                'password': '',
                'gate_device_id': 348,
                'open_gate_scenario': 21,
                'close_gate_scenario': 22,
                'notification_agent_id': 7
            },
            'gate': {
                'auto_close_timeout': 300,  # 5 minutes
                'session_timeout': 60,      # 1 minute
                'status_check_interval': 30,
                'ble_scan_interval': 5
            },
            'tokens': {
                'registered': []
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/gate_controller.log'
            }
        }

    def save(self):
        """Save current configuration to file."""
        os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

    # C4 Configuration
    @property
    def c4_ip(self) -> str:
        """Get Control4 controller IP address."""
        return self.config.get('c4', {}).get('ip', '')

    @property
    def c4_username(self) -> str:
        """Get Control4 account username."""
        return self.config.get('c4', {}).get('username', '')

    @property
    def c4_password(self) -> str:
        """Get Control4 account password."""
        return self.config.get('c4', {}).get('password', '')

    @property
    def gate_device_id(self) -> int:
        """Get gate device ID."""
        return self.config.get('c4', {}).get('gate_device_id', 348)

    @property
    def open_gate_scenario(self) -> int:
        """Get scenario number for opening gate."""
        return self.config.get('c4', {}).get('open_gate_scenario', 21)

    @property
    def close_gate_scenario(self) -> int:
        """Get scenario number for closing gate."""
        return self.config.get('c4', {}).get('close_gate_scenario', 22)

    @property
    def notification_agent_id(self) -> int:
        """Get notification agent ID."""
        return self.config.get('c4', {}).get('notification_agent_id', 7)

    # Gate Configuration
    @property
    def auto_close_timeout(self) -> int:
        """Get auto-close timeout in seconds."""
        return self.config.get('gate', {}).get('auto_close_timeout', 300)

    @property
    def session_timeout(self) -> int:
        """Get session timeout in seconds."""
        return self.config.get('gate', {}).get('session_timeout', 60)

    @property
    def status_check_interval(self) -> int:
        """Get status check interval in seconds."""
        return self.config.get('gate', {}).get('status_check_interval', 30)

    @property
    def ble_scan_interval(self) -> int:
        """Get BLE scan interval in seconds."""
        return self.config.get('gate', {}).get('ble_scan_interval', 5)

    # Token Configuration
    @property
    def registered_tokens(self) -> List[Dict[str, str]]:
        """Get list of registered tokens."""
        return self.config.get('tokens', {}).get('registered', [])

    def add_token(self, uuid: str, name: str, active: bool = True) -> bool:
        """Add a token to registered list.
        
        Args:
            uuid: Token UUID
            name: User-friendly name
            active: Whether token is active (default: True)
            
        Returns:
            True if added, False if already exists
        """
        tokens = self.registered_tokens
        
        # Check if already exists
        for token in tokens:
            if token.get('uuid') == uuid:
                return False
        
        # Add new token with active attribute
        tokens.append({'uuid': uuid, 'name': name, 'active': active})
        
        if 'tokens' not in self.config:
            self.config['tokens'] = {}
        self.config['tokens']['registered'] = tokens
        
        return True
    
    def update_token(self, uuid: str, name: str = None, active: bool = None) -> bool:
        """Update a token's attributes.
        
        Args:
            uuid: Token UUID
            name: New name (optional)
            active: New active status (optional)
            
        Returns:
            True if updated, False if not found
        """
        tokens = self.registered_tokens
        
        for token in tokens:
            if token.get('uuid') == uuid:
                if name is not None:
                    token['name'] = name
                if active is not None:
                    token['active'] = active
                # Update config
                self.config['tokens']['registered'] = tokens
                return True
        
        return False

    def remove_token(self, uuid: str) -> bool:
        """Remove a token from registered list.
        
        Args:
            uuid: Token UUID
            
        Returns:
            True if removed, False if not found
        """
        tokens = self.registered_tokens
        initial_len = len(tokens)
        
        # Remove matching token
        tokens = [t for t in tokens if t.get('uuid') != uuid]
        
        if len(tokens) == initial_len:
            return False
        
        if 'tokens' not in self.config:
            self.config['tokens'] = {}
        self.config['tokens']['registered'] = tokens
        
        return True

    # Logging Configuration
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.config.get('logging', {}).get('level', 'INFO')

    @property
    def log_file(self) -> str:
        """Get log file path."""
        return self.config.get('logging', {}).get('file', 'logs/gate_controller.log')

