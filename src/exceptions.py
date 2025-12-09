"""Centralized exception hierarchy for FigmaForge."""


class FigmaForgeError(Exception):
    """Base exception for all FigmaForge errors."""
    pass


# Figma API Errors
class FigmaAPIError(FigmaForgeError):
    """Base exception for Figma API errors."""
    pass


class FigmaAuthError(FigmaAPIError):
    """Authentication failed - invalid or missing token."""
    pass


class FigmaRateLimitError(FigmaAPIError):
    """API rate limit exceeded."""
    pass


class FigmaNotFoundError(FigmaAPIError):
    """Resource (file or node) not found."""
    pass


class FigmaConnectionError(FigmaAPIError):
    """Network connection failed."""
    pass


# Generation Errors
class GenerationError(FigmaForgeError):
    """Base exception for code generation errors."""
    pass


class NodeNotFoundError(GenerationError):
    """Requested node ID not found in Figma file."""
    pass


class AssetDownloadError(GenerationError):
    """Failed to download asset from Figma."""
    pass


class InvalidComponentNameError(GenerationError):
    """Component name is invalid or cannot be sanitized."""
    pass


# Configuration Errors
class ConfigurationError(FigmaForgeError):
    """Configuration is missing or invalid."""
    pass


class MissingTokenError(ConfigurationError):
    """FIGMA_TOKEN environment variable not set."""
    def __init__(self):
        super().__init__(
            "FIGMA_TOKEN not set. Get one at: https://www.figma.com/settings"
        )
