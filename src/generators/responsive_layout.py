"""Responsive layout converter using Flexbox/Grid instead of absolute positioning.

This module provides an alternative to the default absolute-position layout,
generating CSS that uses modern layout techniques for responsive designs.
"""

from typing import Dict, List, Optional, Tuple
from ..figma.types import FigmaNode


class ResponsiveLayoutConverter:
    """Generates responsive CSS layouts using Flexbox and Grid.
    
    This converter analyzes Figma auto-layout and constraints to generate
    CSS that adapts to different screen sizes, instead of using fixed
    pixel positioning.
    """
    
    # Breakpoints for responsive design
    BREAKPOINTS = {
        "sm": 640,
        "md": 768,
        "lg": 1024,
        "xl": 1280,
    }
    
    def __init__(self, use_percentage_widths: bool = True, use_rem: bool = True):
        """Initialize responsive converter.
        
        Args:
            use_percentage_widths: If True, use percentage widths for containers
            use_rem: If True, use rem units for spacing (1rem = 16px)
        """
        self.use_percentage_widths = use_percentage_widths
        self.use_rem = use_rem
        self.root_width = 0
        self.root_height = 0
    
    def convert_layout(
        self,
        node: FigmaNode,
        parent: FigmaNode = None,
        root_bounds: Dict = None,
        is_root: bool = False
    ) -> Dict[str, str]:
        """Convert Figma layout to responsive CSS.
        
        This differs from LayoutConverter by:
        - Using flexbox/grid for container layouts
        - Using relative units (%, rem) instead of px where sensible
        - Respecting Figma constraints for responsive behavior
        """
        styles: Dict[str, str] = {}
        
        if is_root:
            bounds = node.get("absoluteBoundingBox", {})
            self.root_width = bounds.get("width", 1440)  # Default to 1440px if no bounds
            self.root_height = bounds.get("height", 900)
            styles["position"] = "relative"
            styles["width"] = "100%"
            # Only set max-width if we have a valid root width
            if self.root_width > 0:
                styles["max-width"] = f"{self.root_width}px"
            styles["margin"] = "0 auto"
            styles["min-height"] = f"{self.root_height}px"  # Preserve min height
        else:
            # Check layout mode of parent for flow understanding
            parent_layout = parent.get("layoutMode", "NONE") if parent else "NONE"
            
            if parent_layout in ["HORIZONTAL", "VERTICAL"]:
                # Child of flex container - use flex child styles
                styles.update(self._flex_child_styles(node, parent))
            else:
                # Non-auto-layout parent - use relative positioning with percentage layout
                styles.update(self._smart_positioning(node, root_bounds))
        
        # Apply auto-layout if present
        layout_mode = node.get("layoutMode", "NONE")
        if layout_mode in ["HORIZONTAL", "VERTICAL"]:
            styles.update(self._flexbox_container(node))
        
        # Apply padding
        styles.update(self._padding_styles(node))
        
        # Apply gap/spacing
        if (spacing := node.get("itemSpacing", 0)) > 0:
            styles["gap"] = self._to_unit(spacing)
        
        return styles
    
    def _flexbox_container(self, node: FigmaNode) -> Dict[str, str]:
        """Generate flexbox container styles from Figma auto-layout."""
        styles = {"display": "flex"}
        
        layout_mode = node.get("layoutMode")
        styles["flex-direction"] = "row" if layout_mode == "HORIZONTAL" else "column"
        
        # Wrapping
        if node.get("layoutWrap") == "WRAP":
            styles["flex-wrap"] = "wrap"
        
        # Alignment mapping
        alignment_map = {
            "MIN": "flex-start",
            "CENTER": "center",
            "MAX": "flex-end",
            "SPACE_BETWEEN": "space-between",
            "STRETCH": "stretch",
        }
        
        primary = node.get("primaryAxisAlignItems", "MIN")
        counter = node.get("counterAxisAlignItems", "MIN")
        
        styles["justify-content"] = alignment_map.get(primary, "flex-start")
        styles["align-items"] = alignment_map.get(counter, "flex-start")
        
        return styles
    
    def _flex_child_styles(self, node: FigmaNode, parent: FigmaNode) -> Dict[str, str]:
        """Generate styles for a flex child based on sizing constraints."""
        styles = {}
        
        # Figma sizing modes
        primary_sizing = node.get("primaryAxisSizingMode", "AUTO")
        counter_sizing = node.get("counterAxisSizingMode", "AUTO")
        layout_grow = node.get("layoutGrow", 0)
        
        parent_dir = parent.get("layoutMode", "HORIZONTAL")
        bounds = node.get("absoluteBoundingBox", {})
        
        # Handle flex-grow
        if layout_grow > 0:
            styles["flex-grow"] = str(layout_grow)
        
        # Width/height based on sizing mode
        if parent_dir == "HORIZONTAL":
            # Width is in the main axis direction
            if primary_sizing == "FIXED":
                w = bounds.get("width", 0)
                if self.use_percentage_widths and self.root_width > 0:
                    pct = (w / self.root_width) * 100
                    styles["width"] = f"{pct:.1f}%"
                else:
                    styles["width"] = f"{w}px"
            elif primary_sizing == "FILL":
                styles["flex"] = "1"
            # Counter axis (height)
            if counter_sizing == "FIXED":
                h = bounds.get("height", 0)
                styles["height"] = f"{h}px"
            elif counter_sizing == "FILL":
                styles["align-self"] = "stretch"
        else:
            # Height is in the main axis direction
            if primary_sizing == "FIXED":
                h = bounds.get("height", 0)
                styles["height"] = f"{h}px"
            elif primary_sizing == "FILL":
                styles["flex"] = "1"
            # Counter axis (width)
            if counter_sizing == "FIXED":
                w = bounds.get("width", 0)
                if self.use_percentage_widths and self.root_width > 0:
                    pct = (w / self.root_width) * 100
                    styles["width"] = f"{pct:.1f}%"
                else:
                    styles["width"] = f"{w}px"
            elif counter_sizing == "FILL":
                styles["align-self"] = "stretch"
        
        return styles
    
    def _smart_positioning(self, node: FigmaNode, root_bounds: Dict) -> Dict[str, str]:
        """Generate smarter positioning using constraints."""
        styles = {}
        constraints = node.get("constraints", {})
        bounds = node.get("absoluteBoundingBox", {})
        
        horizontal = constraints.get("horizontal", "MIN")
        vertical = constraints.get("vertical", "MIN")
        
        # For non-auto-layout containers, we use a hybrid approach
        # that respects constraints while still being somewhat responsive
        
        node_w = bounds.get("width", 0)
        node_h = bounds.get("height", 0)
        
        if root_bounds:
            root_w = root_bounds.get("width", 0)
            root_h = root_bounds.get("height", 0)
            node_x = bounds.get("x", 0) - root_bounds.get("x", 0)
            node_y = bounds.get("y", 0) - root_bounds.get("y", 0)
        else:
            root_w, root_h = self.root_width, self.root_height
            node_x = bounds.get("x", 0)
            node_y = bounds.get("y", 0)
        
        # Handle horizontal constraint
        if horizontal == "STRETCH":
            styles["position"] = "absolute"
            left_pct = (node_x / root_w * 100) if root_w else 0
            right_dist = root_w - node_x - node_w
            right_pct = (right_dist / root_w * 100) if root_w else 0
            styles["left"] = f"{left_pct:.1f}%"
            styles["right"] = f"{right_pct:.1f}%"
        elif horizontal == "CENTER":
            styles["position"] = "absolute"
            center_pct = ((node_x + node_w/2) / root_w * 100) if root_w else 50
            styles["left"] = f"{center_pct:.1f}%"
            styles["transform"] = "translateX(-50%)"
            styles["width"] = f"{node_w}px"
        elif horizontal == "MAX":
            styles["position"] = "absolute"
            right_dist = root_w - node_x - node_w
            styles["right"] = f"{right_dist}px"
            styles["width"] = f"{node_w}px"
        elif horizontal == "SCALE":
            styles["position"] = "absolute"
            left_pct = (node_x / root_w * 100) if root_w else 0
            width_pct = (node_w / root_w * 100) if root_w else 100
            styles["left"] = f"{left_pct:.1f}%"
            styles["width"] = f"{width_pct:.1f}%"
        else:  # MIN (default)
            styles["position"] = "absolute"
            styles["left"] = f"{node_x}px"
            styles["width"] = f"{node_w}px"
        
        # Handle vertical constraint
        if vertical == "STRETCH":
            top_pct = (node_y / root_h * 100) if root_h else 0
            bottom_dist = root_h - node_y - node_h
            bottom_pct = (bottom_dist / root_h * 100) if root_h else 0
            styles["top"] = f"{top_pct:.1f}%"
            styles["bottom"] = f"{bottom_pct:.1f}%"
        elif vertical == "CENTER":
            center_pct = ((node_y + node_h/2) / root_h * 100) if root_h else 50
            styles["top"] = f"{center_pct:.1f}%"
            # Combine transforms if needed
            if "transform" in styles:
                styles["transform"] = "translate(-50%, -50%)"
            else:
                styles["transform"] = "translateY(-50%)"
            styles["height"] = f"{node_h}px"
        elif vertical == "MAX":
            bottom_dist = root_h - node_y - node_h
            styles["bottom"] = f"{bottom_dist}px"
            styles["height"] = f"{node_h}px"
        elif vertical == "SCALE":
            top_pct = (node_y / root_h * 100) if root_h else 0
            height_pct = (node_h / root_h * 100) if root_h else 100
            styles["top"] = f"{top_pct:.1f}%"
            styles["height"] = f"{height_pct:.1f}%"
        else:  # MIN (default)
            styles["top"] = f"{node_y}px"
            styles["height"] = f"{node_h}px"
        
        return styles
    
    def _padding_styles(self, node: FigmaNode) -> Dict[str, str]:
        """Generate padding styles."""
        styles = {}
        
        top = node.get("paddingTop", 0)
        right = node.get("paddingRight", 0)
        bottom = node.get("paddingBottom", 0)
        left = node.get("paddingLeft", 0)
        
        if top == right == bottom == left:
            if top > 0:
                styles["padding"] = self._to_unit(top)
        else:
            if top > 0:
                styles["padding-top"] = self._to_unit(top)
            if right > 0:
                styles["padding-right"] = self._to_unit(right)
            if bottom > 0:
                styles["padding-bottom"] = self._to_unit(bottom)
            if left > 0:
                styles["padding-left"] = self._to_unit(left)
        
        return styles
    
    def _to_unit(self, px_value: float) -> str:
        """Convert pixel value to appropriate unit."""
        if self.use_rem:
            return f"{px_value / 16:.3f}rem".rstrip('0').rstrip('.')
        return f"{px_value}px"
    
    def generate_media_queries(
        self,
        node: FigmaNode,
        base_styles: Dict[str, str]
    ) -> Dict[str, Dict[str, str]]:
        """Generate responsive overrides for different breakpoints.
        
        Returns:
            Dict mapping breakpoint names to style overrides
        """
        overrides = {}
        
        bounds = node.get("absoluteBoundingBox", {})
        node_width = bounds.get("width", 0)
        
        # If element is wider than mobile breakpoint, add responsive adjustments
        if node_width > self.BREAKPOINTS["sm"]:
            overrides["sm"] = {
                "width": "100%",
                "max-width": "none",
            }
        
        return overrides
