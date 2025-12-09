"""Extract design tokens from Figma documents."""

import json
from typing import Dict, Any, List, Set
from ..figma.types import FigmaNode, DesignTokens
from ..utils.console import console
from ..utils.colors import rgba_to_hex, get_semantic_color_name
from ..utils.css import effect_to_shadow


class TokenExtractor:
    """Extracts colors, typography, spacing, and other tokens from Figma nodes."""
    
    def __init__(self):
        self.colors: Set[str] = set()
        self.typography: Dict[str, Dict[str, Any]] = {}
        self.spacing_values: Set[float] = set()
        self.radii: Set[float] = set()
        self.shadows: List[str] = []
        self.font_families: Set[str] = set()
    
    def extract_tokens(self, nodes: Dict[str, FigmaNode]) -> DesignTokens:
        """Extract design tokens from a set of Figma nodes."""
        console.print("[cyan]🎨 Extracting design tokens...[/cyan]")
        
        # Reset state
        self.colors = set()
        self.typography = {}
        self.spacing_values = set()
        self.radii = set()
        self.shadows = []
        self.font_families = set()
        
        for node in nodes.values():
            self._extract_from_node(node)
        
        tokens: DesignTokens = {
            "colors": self._build_color_tokens(),
            "typography": self.typography,
            "spacing": self._build_spacing_tokens(),
            "radii": self._build_radii_tokens(),
            "shadows": self._build_shadow_tokens(),
            "fontFamilies": list(self.font_families)
        }
        
        console.print("[green]✓ Extracted tokens:[/green]")
        console.print(f"  • {len(tokens['colors'])} colors")
        console.print(f"  • {len(tokens['typography'])} typography styles")
        console.print(f"  • {len(tokens['spacing'])} spacing values")
        console.print(f"  • {len(tokens['radii'])} border radii")
        console.print(f"  • {len(tokens['shadows'])} shadows")
        
        return tokens
    
    def save_tokens(self, tokens: DesignTokens, output_path: str) -> None:
        """Save tokens to a JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✓ Saved tokens to: {output_path}[/green]")
    
    def _extract_from_node(self, node: FigmaNode) -> None:
        """Recursively extract tokens from a node and its children."""
        # Colors from fills
        for fill in node.get("fills", []):
            if fill.get("visible", True) and fill.get("type") == "SOLID":
                if color := fill.get("color"):
                    self.colors.add(rgba_to_hex(color))
        
        # Colors from strokes
        for stroke in node.get("strokes", []):
            if stroke.get("visible", True) and stroke.get("type") == "SOLID":
                if color := stroke.get("color"):
                    self.colors.add(rgba_to_hex(color))
        
        # Typography from text nodes
        if node.get("type") == "TEXT":
            style = node.get("style", {})
            if font_family := style.get("fontFamily"):
                self.font_families.add(font_family)
                
                style_key = self._get_typography_key(style)
                if style_key not in self.typography:
                    self.typography[style_key] = {
                        "fontFamily": font_family,
                        "fontSize": f"{style.get('fontSize', 16)}px",
                        "fontWeight": style.get("fontWeight", 400),
                        "lineHeight": self._get_line_height(style),
                        "letterSpacing": f"{style.get('letterSpacing', 0)}px"
                    }
        
        # Spacing from layout
        for prop in ["paddingLeft", "paddingRight", "paddingTop", "paddingBottom", "itemSpacing"]:
            if (value := node.get(prop)) and value > 0:
                self.spacing_values.add(value)
        
        # Border radius
        if (radius := node.get("cornerRadius")) and radius > 0:
            self.radii.add(radius)
        
        for radius in node.get("rectangleCornerRadii", []):
            if radius > 0:
                self.radii.add(radius)
        
        # Shadows
        for effect in node.get("effects", []):
            if effect.get("visible", True) and effect.get("type") in ["DROP_SHADOW", "INNER_SHADOW"]:
                shadow = effect_to_shadow(effect)
                if shadow not in self.shadows:
                    self.shadows.append(shadow)
        
        # Process children
        for child in node.get("children", []):
            if isinstance(child, dict):
                self._extract_from_node(child)
    
    def _build_color_tokens(self) -> Dict[str, str]:
        """Build color tokens with semantic names where possible."""
        colors_list = sorted(self.colors)
        tokens = {}
        
        for i, color in enumerate(colors_list, 1):
            name = get_semantic_color_name(color) or f"color-{i}"
            tokens[name] = color
        
        return tokens
    
    def _build_spacing_tokens(self) -> Dict[str, str]:
        """Build spacing scale tokens."""
        scale_names = ["xs", "sm", "md", "lg", "xl", "2xl", "3xl", "4xl", "5xl"]
        tokens = {}
        
        for i, value in enumerate(sorted(self.spacing_values)):
            name = scale_names[i] if i < len(scale_names) else f"spacing-{i + 1}"
            tokens[name] = f"{value}px"
        
        return tokens
    
    def _build_radii_tokens(self) -> Dict[str, str]:
        """Build border radius tokens."""
        scale_names = ["sm", "md", "lg", "xl", "2xl", "3xl", "full"]
        tokens = {}
        
        for i, value in enumerate(sorted(self.radii)):
            name = scale_names[i] if i < len(scale_names) else f"radius-{i + 1}"
            tokens[name] = f"{value}px"
        
        return tokens
    
    def _build_shadow_tokens(self) -> Dict[str, str]:
        """Build shadow tokens."""
        scale_names = ["sm", "md", "lg", "xl", "2xl"]
        tokens = {}
        
        for i, shadow in enumerate(self.shadows):
            name = scale_names[i] if i < len(scale_names) else f"shadow-{i + 1}"
            tokens[name] = shadow
        
        return tokens
    
    @staticmethod
    def _get_typography_key(style: Dict[str, Any]) -> str:
        return f"{style.get('fontFamily', 'default')}-{style.get('fontSize', 16)}-{style.get('fontWeight', 400)}"
    
    @staticmethod
    def _get_line_height(style: Dict[str, Any]) -> str:
        unit = style.get("lineHeightUnit", "PIXELS")
        if unit == "PIXELS":
            return f"{style.get('lineHeightPx', 24)}px"
        elif unit == "FONT_SIZE_%":
            return f"{style.get('lineHeightPercent', 100) / 100}"
        return "normal"
