"""Token management for gate controller."""

from typing import List, Dict, Optional
from ..config.config import Config
from ..utils.logger import get_logger


def normalize_uuid(uuid: str) -> str:
    """Normalize UUID by converting to lowercase and removing dashes.
    
    Args:
        uuid: UUID string (with or without dashes)
        
    Returns:
        Normalized UUID (lowercase, no dashes)
    """
    return uuid.lower().replace('-', '')


class TokenManager:
    """Manager for BLE token registration and storage."""

    def __init__(self, config: Config):
        """Initialize token manager.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.logger = get_logger(__name__)

    def register_token(self, uuid: str, name: str, active: bool = True) -> bool:
        """Register a new BLE token.
        
        Args:
            uuid: Token UUID (BLE address or identifier)
            name: User-friendly name for the token
            active: Whether token is active (default: True)
            
        Returns:
            True if registered successfully, False if already exists
        """
        uuid = uuid.lower()  # Normalize to lowercase
        
        # Check if already registered
        if self.is_token_registered(uuid):
            self.logger.warning(f"Token {uuid} is already registered")
            return False
        
        # Add to config with active status
        success = self.config.add_token(uuid, name, active)
        
        if success:
            # Save configuration
            self.config.save()
            self.logger.info(f"Registered token: {name} ({uuid}) [active={active}]")
        
        return success
    
    def update_token(self, uuid: str, name: str = None, active: bool = None) -> bool:
        """Update a token's attributes.
        
        Args:
            uuid: Token UUID
            name: New name (optional)
            active: New active status (optional)
            
        Returns:
            True if updated successfully, False if not found
        """
        uuid = uuid.lower()  # Normalize to lowercase
        
        success = self.config.update_token(uuid, name, active)
        
        if success:
            # Save configuration
            self.config.save()
            updates = []
            if name is not None:
                updates.append(f"name='{name}'")
            if active is not None:
                updates.append(f"active={active}")
            self.logger.info(f"Updated token {uuid}: {', '.join(updates)}")
        else:
            self.logger.warning(f"Token {uuid} not found")
        
        return success

    def unregister_token(self, uuid: str) -> bool:
        """Unregister a BLE token.
        
        Args:
            uuid: Token UUID
            
        Returns:
            True if unregistered successfully, False if not found
        """
        uuid = uuid.lower()  # Normalize to lowercase
        
        success = self.config.remove_token(uuid)
        
        if success:
            # Save configuration
            self.config.save()
            self.logger.info(f"Unregistered token: {uuid}")
        else:
            self.logger.warning(f"Token {uuid} not found")
        
        return success

    def get_all_tokens(self) -> List[Dict[str, str]]:
        """Get all registered tokens.
        
        Returns:
            List of token dicts with 'uuid' and 'name'
        """
        return self.config.registered_tokens

    def get_token_by_uuid(self, uuid: str) -> Optional[Dict[str, str]]:
        """Get token information by UUID.
        
        Args:
            uuid: Token UUID (with or without dashes)
            
        Returns:
            Token dict with 'uuid' and 'name', or None if not found
        """
        uuid_normalized = normalize_uuid(uuid)  # Normalize: lowercase, no dashes
        
        for token in self.config.registered_tokens:
            token_uuid_normalized = normalize_uuid(token.get('uuid', ''))
            if token_uuid_normalized == uuid_normalized:
                return token
        
        return None

    def is_token_registered(self, uuid: str) -> bool:
        """Check if a token is registered.
        
        Args:
            uuid: Token UUID
            
        Returns:
            True if registered, False otherwise
        """
        return self.get_token_by_uuid(uuid) is not None

    def get_token_count(self) -> int:
        """Get number of registered tokens.
        
        Returns:
            Number of registered tokens
        """
        return len(self.config.registered_tokens)

