"""Normalizes Figma document structure for component generation."""

from typing import List, Dict, Any, Optional
from .types import FigmaNode, FigmaComponent, FigmaFile
from ..utils.console import console


class FigmaNormalizer:
    """Processes Figma documents and extracts component information."""
    
    COMPONENT_TYPES = {"COMPONENT", "COMPONENT_SET", "FRAME", "INSTANCE"}
    LEAF_TYPES = {"TEXT", "VECTOR", "RECTANGLE", "ELLIPSE", "LINE", "STAR", "REGULAR_POLYGON"}
    
    def __init__(self):
        self.components: List[FigmaComponent] = []
        self.all_nodes: Dict[str, FigmaNode] = {}
    
    def normalize_file(self, file_data: FigmaFile) -> Dict[str, Any]:
        """Normalize a Figma file into a structured format with components and metadata."""
        console.print("[cyan]🔄 Normalizing Figma file structure...[/cyan]")
        
        self.components = []
        self.all_nodes = {}
        
        document = file_data.get("document")
        if not document:
            console.print("[red]✗ No document found in file data[/red]")
            return {"components": [], "nodes": {}}
        
        self._traverse_node(document)
        console.print(f"[green]✓ Found {len(self.components)} component(s)[/green]")
        
        return {
            "file_name": file_data.get("name", "Untitled"),
            "last_modified": file_data.get("lastModified"),
            "version": file_data.get("version"),
            "components": self.components,
            "nodes": self.all_nodes
        }
    
    def normalize_node(self, node: FigmaNode) -> FigmaComponent:
        """Convert a Figma node into a normalized component structure."""
        self.all_nodes[node["id"]] = node
        
        return {
            "id": node["id"],
            "name": self._sanitize_name(node.get("name", "Untitled")),
            "node": node,
            "tokens": self._extract_node_tokens(node),
            "assets": self._find_asset_nodes(node)
        }
    
    def _traverse_node(self, node: FigmaNode, parent_path: str = "") -> None:
        """Recursively traverse node tree and collect components."""
        node_id = node.get("id", "unknown")
        node_type = node.get("type", "UNKNOWN")
        node_name = node.get("name", "Untitled")
        
        self.all_nodes[node_id] = node
        current_path = f"{parent_path}/{node_name}" if parent_path else node_name
        
        if self._is_component_candidate(node):
            component = self.normalize_node(node)
            self.components.append(component)
            console.print(f"  [dim]Found: {component['name']} ({node_type})[/dim]")
        
        for child in node.get("children", []):
            if isinstance(child, dict):
                self._traverse_node(child, current_path)
    
    def _is_component_candidate(self, node: FigmaNode) -> bool:
        """Check if node should be treated as a component."""
        node_type = node.get("type")
        
        if node_type in self.COMPONENT_TYPES:
            return True
        
        # Frames with PascalCase names are treated as components
        if node_type == "FRAME":
            name = node.get("name", "")
            if name and name[0].isupper():
                return True
        
        return False
    
    def _sanitize_name(self, name: str) -> str:
        """Convert Figma name to kebab-case for Angular components."""
        name = name.lower()
        name = name.replace("/", "-").replace("\\", "-")
        name = name.replace(" ", "-").replace("_", "-")
        name = "".join(c for c in name if c.isalnum() or c == "-")
        
        while "--" in name:
            name = name.replace("--", "-")
        
        name = name.strip("-")
        
        if name and not name[0].isalpha():
            name = "component-" + name
        
        return name or "component"
    
    def _extract_node_tokens(self, node: FigmaNode) -> Dict[str, Any]:
        """Extract design tokens from node properties."""
        tokens: Dict[str, Any] = {}
        
        fills = node.get("fills", [])
        if fills:
            fill = fills[0]
            if fill.get("type") == "SOLID" and "color" in fill:
                tokens["backgroundColor"] = self._rgba_to_hex(fill["color"])
        
        if node.get("type") == "TEXT":
            style = node.get("style", {})
            tokens["typography"] = {
                "fontFamily": style.get("fontFamily"),
                "fontSize": style.get("fontSize"),
                "fontWeight": style.get("fontWeight"),
                "lineHeight": style.get("lineHeightPx"),
                "letterSpacing": style.get("letterSpacing")
            }
        
        corner_radius = node.get("cornerRadius")
        if corner_radius is not None:
            tokens["borderRadius"] = f"{corner_radius}px"
        
        for effect in node.get("effects", []):
            if effect.get("visible", True) and effect.get("type") in ["DROP_SHADOW", "INNER_SHADOW"]:
                tokens["boxShadow"] = self._effect_to_css_shadow(effect)
                break
        
        return tokens
    
    def _find_asset_nodes(self, node: FigmaNode) -> List[str]:
        """Find all exportable asset nodes in a node tree."""
        assets = []
        
        node_type = node.get("type")
        if node_type in {"VECTOR", "RECTANGLE", "ELLIPSE"} and self._has_image_fill(node):
            assets.append(node["id"])
        
        for child in node.get("children", []):
            if isinstance(child, dict):
                assets.extend(self._find_asset_nodes(child))
        
        return assets
    
    def _has_image_fill(self, node: FigmaNode) -> bool:
        fills = node.get("fills", [])
        return any(fill.get("type") == "IMAGE" for fill in fills)
    
    @staticmethod
    def _rgba_to_hex(color: Dict[str, float]) -> str:
        """Convert RGBA (0-1 range) to hex color string."""
        r = int(color.get("r", 0) * 255)
        g = int(color.get("g", 0) * 255)
        b = int(color.get("b", 0) * 255)
        a = color.get("a", 1)
        
        if a < 1:
            return f"#{r:02X}{g:02X}{b:02X}{int(a * 255):02X}"
        return f"#{r:02X}{g:02X}{b:02X}"
    
    @staticmethod
    def _effect_to_css_shadow(effect: Dict[str, Any]) -> str:
        """Convert Figma effect to CSS box-shadow."""
        offset = effect.get("offset", {})
        x, y = offset.get("x", 0), offset.get("y", 0)
        radius = effect.get("radius", 0)
        spread = effect.get("spread", 0)
        
        color_str = FigmaNormalizer._rgba_to_hex(effect.get("color", {}))
        inset = "inset " if effect.get("type") == "INNER_SHADOW" else ""
        
        return f"{inset}{x}px {y}px {radius}px {spread}px {color_str}"
