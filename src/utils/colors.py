"""Color conversion utilities for FigmaForge."""

from typing import Dict, Tuple


def rgba_to_hex(color: Dict[str, float]) -> str:
    """Convert Figma RGBA (0-1 range) to CSS hex color.
    
    Args:
        color: Dict with r, g, b (0-1) and optional a
        
    Returns:
        Hex color string (#RRGGBB or #RRGGBBAA)
    """
    r = int(color.get("r", 0) * 255)
    g = int(color.get("g", 0) * 255)
    b = int(color.get("b", 0) * 255)
    a = color.get("a", 1.0)
    
    if a < 1.0:
        return f"#{r:02X}{g:02X}{b:02X}{int(a * 255):02X}"
    return f"#{r:02X}{g:02X}{b:02X}"


def rgba_to_css(color: Dict[str, float], opacity: float = 1.0) -> str:
    """Convert Figma RGBA to CSS rgba() function.
    
    Args:
        color: Dict with r, g, b, a (0-1 range)
        opacity: Additional opacity multiplier
        
    Returns:
        CSS rgba() string
    """
    r = int(color.get("r", 0) * 255)
    g = int(color.get("g", 0) * 255)
    b = int(color.get("b", 0) * 255)
    a = color.get("a", 1.0) * opacity
    
    return f"rgba({r}, {g}, {b}, {a:.2f})"


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple.
    
    Args:
        hex_color: Hex color string (#RGB, #RRGGBB, or #RRGGBBAA)
        
    Returns:
        Tuple of (r, g, b) in 0-255 range
    """
    hex_color = hex_color.lstrip("#")
    
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    return (r, g, b)


def get_semantic_color_name(hex_color: str) -> str:
    """Try to match hex color to a semantic name.
    
    Args:
        hex_color: Hex color string
        
    Returns:
        Semantic name or empty string
    """
    known_colors = {
        "#FFFFFF": "white",
        "#000000": "black",
        "#FF0000": "red",
        "#00FF00": "green",
        "#0000FF": "blue",
        "#FFFF00": "yellow",
        "#FF00FF": "magenta",
        "#00FFFF": "cyan",
        "#808080": "gray",
    }
    return known_colors.get(hex_color.upper(), "")
