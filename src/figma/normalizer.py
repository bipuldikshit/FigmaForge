"""Normalizes Figma document structure for component generation."""

from typing import List, Dict, Any
from .types import FigmaNode, FigmaComponent, FigmaFile
from ..utils.console import console
from ..utils.colors import rgba_to_hex
from ..utils.css import effect_to_shadow, sanitize_css_class


class FigmaNormalizer:
    """Processes Figma documents and extracts component information."""
    
    COMPONENT_TYPES = {"COMPONENT", "COMPONENT_SET", "FRAME", "INSTANCE"}
    LEAF_TYPES = {"TEXT", "VECTOR", "RECTANGLE", "ELLIPSE", "LINE", "STAR", "REGULAR_POLYGON"}
    
    def __init__(self):
        self.components: List[FigmaComponent] = []
        self.all_nodes: Dict[str, FigmaNode] = {}
    
    def normalize_file(self, file_data: FigmaFile) -> Dict[str, Any]:
        """Normalize a Figma file into a structured format."""
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
            "name": sanitize_css_class(node.get("name", "Untitled")),
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
        
        if node_type == "FRAME":
            name = node.get("name", "")
            if name and name[0].isupper():
                return True
        
        return False
    
    def _extract_node_tokens(self, node: FigmaNode) -> Dict[str, Any]:
        """Extract design tokens from node properties."""
        tokens: Dict[str, Any] = {}
        
        fills = node.get("fills", [])
        if fills:
            fill = fills[0]
            if fill.get("type") == "SOLID" and "color" in fill:
                tokens["backgroundColor"] = rgba_to_hex(fill["color"])
        
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
                tokens["boxShadow"] = effect_to_shadow(effect)
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
