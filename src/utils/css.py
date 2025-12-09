"""CSS generation utilities for FigmaForge."""

from typing import Dict, Any


def effect_to_shadow(effect: Dict[str, Any]) -> str:
    """Convert Figma effect to CSS box-shadow.
    
    Args:
        effect: Figma DROP_SHADOW or INNER_SHADOW effect
        
    Returns:
        CSS box-shadow value
    """
    offset = effect.get("offset", {})
    x = offset.get("x", 0)
    y = offset.get("y", 0)
    radius = effect.get("radius", 0)
    spread = effect.get("spread", 0)
    
    color = effect.get("color", {})
    r = int(color.get("r", 0) * 255)
    g = int(color.get("g", 0) * 255)
    b = int(color.get("b", 0) * 255)
    a = color.get("a", 1)
    
    inset = "inset " if effect.get("type") == "INNER_SHADOW" else ""
    return f"{inset}{x}px {y}px {radius}px {spread}px rgba({r}, {g}, {b}, {a})"


def fill_to_background(fill: Dict[str, Any]) -> str:
    """Convert Figma fill to CSS background value.
    
    Supports SOLID, GRADIENT_LINEAR, and GRADIENT_RADIAL fills.
    
    Args:
        fill: Figma fill object
        
    Returns:
        CSS background/background-color value
    """
    fill_type = fill.get("type", "SOLID")
    
    if fill_type == "SOLID":
        color = fill.get("color", {})
        opacity = fill.get("opacity", 1.0)
        return _rgba_to_css(color, opacity)
    
    elif fill_type == "GRADIENT_LINEAR":
        return _linear_gradient_to_css(fill)
    
    elif fill_type == "GRADIENT_RADIAL":
        return _radial_gradient_to_css(fill)
    
    elif fill_type == "GRADIENT_ANGULAR":
        return _angular_gradient_to_css(fill)
    
    # Fallback for unsupported types (IMAGE, etc.)
    return ""


def _linear_gradient_to_css(fill: Dict[str, Any]) -> str:
    """Convert Figma linear gradient to CSS linear-gradient()."""
    gradient_handles = fill.get("gradientHandlePositions", [])
    gradient_stops = fill.get("gradientStops", [])
    
    if not gradient_stops:
        return ""
    
    # Calculate angle from handle positions
    angle = 180  # Default: top to bottom
    if len(gradient_handles) >= 2:
        start = gradient_handles[0]
        end = gradient_handles[1]
        import math
        dx = end.get("x", 0) - start.get("x", 0)
        dy = end.get("y", 0) - start.get("y", 0)
        angle = math.degrees(math.atan2(dy, dx)) + 90
        angle = round(angle) % 360
    
    # Build color stops
    stops = []
    for stop in gradient_stops:
        color = stop.get("color", {})
        position = stop.get("position", 0) * 100
        stops.append(f"{_rgba_to_css(color)} {position:.0f}%")
    
    return f"linear-gradient({angle}deg, {', '.join(stops)})"


def _radial_gradient_to_css(fill: Dict[str, Any]) -> str:
    """Convert Figma radial gradient to CSS radial-gradient()."""
    gradient_stops = fill.get("gradientStops", [])
    
    if not gradient_stops:
        return ""
    
    # Build color stops
    stops = []
    for stop in gradient_stops:
        color = stop.get("color", {})
        position = stop.get("position", 0) * 100
        stops.append(f"{_rgba_to_css(color)} {position:.0f}%")
    
    return f"radial-gradient(circle, {', '.join(stops)})"


def _angular_gradient_to_css(fill: Dict[str, Any]) -> str:
    """Convert Figma angular gradient to CSS conic-gradient()."""
    gradient_stops = fill.get("gradientStops", [])
    
    if not gradient_stops:
        return ""
    
    stops = []
    for stop in gradient_stops:
        color = stop.get("color", {})
        position = stop.get("position", 0) * 360
        stops.append(f"{_rgba_to_css(color)} {position:.0f}deg")
    
    return f"conic-gradient(from 0deg, {', '.join(stops)})"


def _rgba_to_css(color: Dict[str, float], opacity: float = 1.0) -> str:
    """Convert Figma RGBA to CSS rgba() function."""
    r = int(color.get("r", 0) * 255)
    g = int(color.get("g", 0) * 255)
    b = int(color.get("b", 0) * 255)
    a = color.get("a", 1.0) * opacity
    
    if a >= 0.99:
        return f"#{r:02X}{g:02X}{b:02X}"
    return f"rgba({r}, {g}, {b}, {a:.2f})"


def format_px(value: float | int, decimals: int = 1) -> str:
    """Format a numeric value as pixel string.
    
    Args:
        value: Numeric value
        decimals: Decimal places (default 1)
        
    Returns:
        Formatted pixel string (e.g., "16px" or "16.5px")
    """
    rounded = round(value, decimals)
    if rounded == int(rounded):
        return f"{int(rounded)}px"
    return f"{rounded}px"


def sanitize_css_class(name: str) -> str:
    """Sanitize a string for use as CSS class name.
    
    Args:
        name: Raw name string
        
    Returns:
        Valid CSS class name in kebab-case
    """
    name = name.lower()
    name = name.replace(" ", "-").replace("/", "-").replace("_", "-")
    name = "".join(c for c in name if c.isalnum() or c == "-")
    
    # Remove consecutive dashes
    while "--" in name:
        name = name.replace("--", "-")
    
    name = name.strip("-")
    
    # Ensure starts with letter
    if name and not name[0].isalpha():
        name = "c-" + name
    
    return name or "element"


def to_camel_case(text: str) -> str:
    """Convert text to camelCase for JavaScript/TypeScript.
    
    Args:
        text: Input text (kebab-case, snake_case, or spaces)
        
    Returns:
        camelCase string
    """
    # Clean special characters
    for char in "<>/\\()[]{}:;,.!?":
        text = text.replace(char, " ")
    text = text.replace("&", "and").replace("+", "plus").replace("=", "equals")
    text = text.replace("-", " ").replace("_", " ")
    
    # Filter stop words
    stop_words = {"the", "a", "an", "to", "for", "of", "in", "on", "at"}
    words = [w for w in text.split() if w and w.lower() not in stop_words]
    
    if not words:
        return "value"
    
    # Build camelCase
    result = words[0].lower()
    for word in words[1:]:
        if word:
            result += word[0].upper() + word[1:].lower()
    
    # Ensure valid identifier
    if not result or not result[0].isalpha():
        result = "value" + result.capitalize()
    
    return "".join(c for c in result if c.isalnum()) or "value"


def to_pascal_case(text: str) -> str:
    """Convert text to PascalCase for class names.
    
    Args:
        text: Input text (kebab-case, snake_case, or spaces)
        
    Returns:
        PascalCase string
    """
    words = text.replace("-", " ").replace("_", " ").split()
    return "".join(word.capitalize() for word in words if word)
