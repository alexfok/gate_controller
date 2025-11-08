"""Token management for gate controller."""

from typing import List, Dict, Optional
from ..config.config import Config
from ..utils.logger import get_logger


class TokenManager:
    """Manager for BLE token registration and storage."""

    def __init__(self, config: Config):
        """Initialize token manager.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.logger = get_logger(__name__)

    def register_token(self, uuid: str, name: str) -> bool:
        """Register a new BLE token.
        
        Args:
            uuid: Token UUID (BLE address or identifier)
            name: User-friendly name for the token
            
        Returns:
            True if registered successfully, False if already exists
        """
        uuid = uuid.lower()  # Normalize to lowercase
        
        # Check if already registered
        if self.is_token_registered(uuid):
            self.logger.warning(f"Token {uuid} is already registered")
            return False
        
        # Add to config
        success = self.config.add_token(uuid, name)
        
        if success:
            # Save configuration
            self.config.save()
            self.logger.info(f"Registered token: {name} ({uuid})")
        
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
            uuid: Token UUID
            
        Returns:
            Token dict with 'uuid' and 'name', or None if not found
        """
        uuid = uuid.lower()  # Normalize to lowercase
        
        for token in self.config.registered_tokens:
            if token.get('uuid', '').lower() == uuid:
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

