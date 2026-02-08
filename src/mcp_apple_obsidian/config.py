"""Configuration management for MCP Apple Obsidian."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ObsidianConfig:
    """Configuration for Obsidian integration."""
    
    # Default vault to use if not specified
    default_vault: Optional[str] = None
    
    # Path to Obsidian app
    obsidian_app_path: str = "/Applications/Obsidian.app"
    
    # Timeout for AppleScript operations (seconds)
    applescript_timeout: int = 30
    
    # Timeout for URI operations (seconds)
    uri_timeout: int = 10
    
    # Maximum file size to read (bytes)
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # Whether to create backup before modifying files
    create_backups: bool = True
    
    # Backup directory
    backup_dir: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "ObsidianConfig":
        """Load configuration from environment variables."""
        return cls(
            default_vault=os.getenv("OBSIDIAN_DEFAULT_VAULT"),
            obsidian_app_path=os.getenv("OBSIDIAN_APP_PATH", "/Applications/Obsidian.app"),
            applescript_timeout=int(os.getenv("OBSIDIAN_APPLESCRIPT_TIMEOUT", "30")),
            uri_timeout=int(os.getenv("OBSIDIAN_URI_TIMEOUT", "10")),
            max_file_size=int(os.getenv("OBSIDIAN_MAX_FILE_SIZE", str(10 * 1024 * 1024))),
            create_backups=os.getenv("OBSIDIAN_CREATE_BACKUPS", "true").lower() == "true",
            backup_dir=os.getenv("OBSIDIAN_BACKUP_DIR"),
        )
    
    def get_backup_directory(self) -> Path:
        """Get the backup directory path."""
        if self.backup_dir:
            return Path(self.backup_dir)
        return Path.home() / ".obsidian-mcp-backups"


# Global configuration instance
_config: Optional[ObsidianConfig] = None


def get_config() -> ObsidianConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = ObsidianConfig.from_env()
    return _config


def set_config(config: ObsidianConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
