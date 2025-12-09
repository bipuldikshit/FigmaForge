"""Centralized configuration for FigmaForge using Pydantic Settings."""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Figma API
    figma_token: str = ""
    figma_api_base_url: str = "https://api.figma.com/v1"
    figma_max_retries: int = 3
    figma_retry_delay: int = 60
    
    # Output paths
    angular_output_path: Path = Path("./src/app/components")
    assets_output_path: Path = Path("./src/assets/figma")
    tokens_output_path: Path = Path("./design-tokens.scss")
    
    # Generation options
    default_style_format: str = "scss"
    inline_svg_threshold: int = 2048  # bytes
    responsive_mode: bool = False  # Use flexbox/responsive layout instead of absolute positioning
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def validate_figma_token() -> bool:
    """Check if Figma token is configured."""
    settings = get_settings()
    return bool(settings.figma_token)
