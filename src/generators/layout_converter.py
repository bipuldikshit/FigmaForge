"""Convert Figma auto-layout to CSS Flexbox with pixel-perfect positioning."""

from typing import Dict, List
from ..figma.types import FigmaNode


class LayoutConverter:
    """Converts Figma layout properties to CSS."""
    
    @staticmethod
    def convert_layout(
        node: FigmaNode,
        parent: FigmaNode = None,
        root_bounds: Dict = None,
        sibling_index: int = 0,
        total_siblings: int = 1
    ) -> Dict[str, str]:
        """Convert Figma layout to CSS styles."""
        styles: Dict[str, str] = {}
        
        if parent is None:
            # Root node uses relative positioning
            styles["position"] = "relative"
            bounds = node.get("absoluteBoundingBox", {})
            styles.update(LayoutConverter._convert_exact_sizing(node))
        else:
            # Children use absolute positioning relative to root
            if root_bounds is None and parent:
                root_bounds = parent.get("absoluteBoundingBox", {})
            
            styles.update(LayoutConverter._convert_relative_positioning(node, root_bounds))
            styles["z-index"] = str(sibling_index + 1)
        
        # Add flex properties if node has auto-layout
        layout_mode = node.get("layoutMode", "NONE")
        if layout_mode in ["HORIZONTAL", "VERTICAL"]:
            styles.update(LayoutConverter._convert_flexbox(node))
        
        styles.update(LayoutConverter._convert_padding(node))
        
        return styles
    
    @staticmethod
    def _convert_relative_positioning(node: FigmaNode, root_bounds: Dict) -> Dict[str, str]:
        """Calculate position relative to root component."""
        styles = {"position": "absolute"}
        
        node_bounds = node.get("absoluteBoundingBox")
        if node_bounds and root_bounds:
            rel_x = node_bounds.get("x", 0) - root_bounds.get("x", 0)
            rel_y = node_bounds.get("y", 0) - root_bounds.get("y", 0)
            
            styles["left"] = f"{rel_x}px"
            styles["top"] = f"{rel_y}px"
            
            if (w := node_bounds.get("width")) is not None:
                styles["width"] = f"{w}px"
            if (h := node_bounds.get("height")) is not None:
                styles["height"] = f"{h}px"
        
        return styles
    
    @staticmethod
    def _convert_exact_sizing(node: FigmaNode) -> Dict[str, str]:
        """Get exact pixel dimensions."""
        styles = {}
        bounds = node.get("absoluteBoundingBox")
        
        if bounds:
            if w := bounds.get("width"):
                styles["width"] = f"{w}px"
            if h := bounds.get("height"):
                styles["height"] = f"{h}px"
        
        return styles
    
    @staticmethod
    def _convert_flexbox(node: FigmaNode) -> Dict[str, str]:
        """Convert Figma auto-layout to flexbox."""
        styles = {"display": "flex"}
        
        layout_mode = node.get("layoutMode")
        styles["flex-direction"] = "row" if layout_mode == "HORIZONTAL" else "column"
        
        if (spacing := node.get("itemSpacing", 0)) > 0:
            styles["gap"] = f"{spacing}px"
        
        align_map = {
            "MIN": "flex-start", "CENTER": "center", "MAX": "flex-end",
            "SPACE_BETWEEN": "space-between", "STRETCH": "stretch"
        }
        
        primary = node.get("primaryAxisAlignItems", "MIN")
        counter = node.get("counterAxisAlignItems", "MIN")
        
        styles["justify-content"] = align_map.get(primary, "flex-start")
        styles["align-items"] = align_map.get(counter, "flex-start")
        
        return styles
    
    @staticmethod
    def _convert_padding(node: FigmaNode) -> Dict[str, str]:
        """Convert padding properties."""
        styles = {}
        
        top = node.get("paddingTop", 0)
        right = node.get("paddingRight", 0)
        bottom = node.get("paddingBottom", 0)
        left = node.get("paddingLeft", 0)
        
        if top == right == bottom == left:
            if top > 0:
                styles["padding"] = f"{top}px"
        else:
            if top > 0:
                styles["padding-top"] = f"{top}px"
            if right > 0:
                styles["padding-right"] = f"{right}px"
            if bottom > 0:
                styles["padding-bottom"] = f"{bottom}px"
            if left > 0:
                styles["padding-left"] = f"{left}px"
        
        return styles
    
    @staticmethod
    def get_responsive_classes(node: FigmaNode) -> List[str]:
        """Generate responsive utility classes from constraints."""
        classes = []
        constraints = node.get("constraints")
        
        if not constraints:
            return classes
        
        horizontal = constraints.get("horizontal", "MIN")
        vertical = constraints.get("vertical", "MIN")
        
        h_map = {"STRETCH": "w-full", "CENTER": "mx-auto", "MAX": "ml-auto", "SCALE": "w-responsive"}
        v_map = {"STRETCH": "h-full", "CENTER": "my-auto", "MAX": "mt-auto", "SCALE": "h-responsive"}
        
        if horizontal in h_map:
            classes.append(h_map[horizontal])
        if vertical in v_map:
            classes.append(v_map[vertical])
        
        return classes
