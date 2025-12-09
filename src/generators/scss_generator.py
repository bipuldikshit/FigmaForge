"""Generate component SCSS styles from Figma nodes."""

from typing import Dict, Any, List
from ..figma.types import FigmaNode
from ..utils.colors import rgba_to_hex, rgba_to_css
from ..utils.css import effect_to_shadow, sanitize_css_class, fill_to_background
from .layout_converter import LayoutConverter
from .responsive_layout import ResponsiveLayoutConverter


class SCSSComponentGenerator:
    """Generates BEM-style SCSS for Angular components.
    
    Note: This generates component-specific styles, not design token variables.
    For design tokens, see extractors/token_scss.py
    """
    
    def __init__(self, component_name: str, responsive_mode: bool = False):
        """Initialize the SCSS generator.
        
        Args:
            component_name: Name of the component for BEM class naming
            responsive_mode: If True, use flexbox/responsive layouts instead of absolute positioning
        """
        self.component_name = component_name
        self.responsive_mode = responsive_mode
        
        if responsive_mode:
            self.layout_converter = ResponsiveLayoutConverter()
        else:
            self.layout_converter = LayoutConverter()
        
        self.generated_classes: Dict[str, Dict[str, str]] = {}
        self.root_bounds = {}
        self.root_node = None
    
    def generate_scss(self, node: FigmaNode, import_tokens: bool = True) -> str:
        """Generate SCSS styles for the component."""
        lines = [
            "// ==================== AUTO-GEN-START ====================",
            "// Generated from Figma - do not modify manually",
            ""
        ]
        
        if import_tokens:
            lines.extend(["@import '../../styles/design-tokens';", ""])
        
        self.root_bounds = node.get("absoluteBoundingBox", {})
        self.root_node = node
        
        # Root class
        root_class = self.component_name
        lines.append(f".{root_class} {{")
        
        root_styles = self._generate_node_styles(node, parent=None, is_root=True)
        for prop, val in root_styles.items():
            lines.append(f"  {prop}: {val};")
        
        lines.extend(["}", ""])
        
        # Child classes
        self._collect_node_styles(node, is_root_call=True)
        
        for class_name, styles in sorted(self.generated_classes.items()):
            if class_name != root_class:
                lines.append(f".{class_name} {{")
                for prop, val in styles.items():
                    lines.append(f"  {prop}: {val};")
                lines.extend(["}", ""])
        
        lines.extend([
            "// ==================== AUTO-GEN-END ====================",
            "",
            "// Custom styles below",
            ""
        ])
        
        return "\n".join(lines)
    
    def _collect_node_styles(self, node: FigmaNode, is_root_call: bool = False) -> None:
        """Collect styles for all child nodes recursively."""
        node_type = node.get("type", "")
        
        if node_type in ["DOCUMENT", "CANVAS"]:
            for child in node.get("children", []):
                if isinstance(child, dict):
                    self._collect_node_styles(child, is_root_call=False)
            return
        
        children = node.get("children", [])
        total = len(children)
        
        for i, child in enumerate(children):
            if isinstance(child, dict):
                class_name = self._generate_class_name(child)
                
                styles = self._generate_node_styles(
                    child,
                    parent=self.root_node if not is_root_call else node,
                    sibling_index=i,
                    total_siblings=total
                )
                
                if styles:
                    self.generated_classes[class_name] = styles
                
                self._collect_node_styles(child, is_root_call=False)
    
    def _generate_node_styles(
        self,
        node: FigmaNode,
        parent: FigmaNode = None,
        is_root: bool = False,
        sibling_index: int = 0,
        total_siblings: int = 1
    ) -> Dict[str, str]:
        """Generate CSS styles for a single node."""
        styles: Dict[str, str] = {}
        
        if is_root:
            styles["box-sizing"] = "border-box"
        
        # Layout
        if self.responsive_mode:
            layout_styles = self.layout_converter.convert_layout(
                node, parent=parent, root_bounds=self.root_bounds, is_root=is_root
            )
        else:
            layout_styles = self.layout_converter.convert_layout(
                node, parent=parent, root_bounds=self.root_bounds,
                sibling_index=sibling_index, total_siblings=total_siblings
            )
        styles.update(layout_styles)
        
        node_type = node.get("type", "")
        
        # Background (supports solid colors and gradients)
        fills = node.get("fills", [])
        if fills and node_type != "TEXT":
            # Process all visible fills (reversed to match CSS layer order)
            backgrounds = []
            for fill in reversed(fills):
                if fill.get("visible", True):
                    bg = fill_to_background(fill)
                    if bg:
                        backgrounds.append(bg)
            
            if backgrounds:
                if len(backgrounds) == 1:
                    styles["background"] = backgrounds[0]
                else:
                    # Multiple fills become layered backgrounds
                    styles["background"] = ", ".join(backgrounds)
        
        # Border
        strokes = node.get("strokes", [])
        if strokes:
            stroke = strokes[0]
            if stroke.get("visible", True) and stroke.get("type") == "SOLID":
                color = stroke.get("color")
                weight = node.get("strokeWeight", 1)
                if color:
                    styles["border"] = f"{weight}px solid {rgba_to_hex(color)}"
        
        # Border radius
        corner_radius = node.get("cornerRadius")
        if corner_radius and corner_radius > 0:
            styles["border-radius"] = f"{round(corner_radius, 1)}px"
        
        corner_radii = node.get("rectangleCornerRadii")
        if corner_radii and len(corner_radii) == 4:
            if not all(r == corner_radii[0] for r in corner_radii):
                styles["border-radius"] = " ".join(f"{r}px" for r in corner_radii)
        
        # Opacity
        if (opacity := node.get("opacity", 1.0)) < 1.0:
            styles["opacity"] = str(opacity)
        
        # Box shadow
        shadows = []
        for effect in node.get("effects", []):
            if effect.get("visible", True) and effect.get("type") in ["DROP_SHADOW", "INNER_SHADOW"]:
                shadows.append(effect_to_shadow(effect))
        if shadows:
            styles["box-shadow"] = ", ".join(shadows)
        
        # Text styles
        if node_type == "TEXT":
            styles.update(self._generate_text_styles(node))
        
        return styles
    
    def _generate_text_styles(self, node: FigmaNode) -> Dict[str, str]:
        """Generate typography styles."""
        styles: Dict[str, str] = {}
        style = node.get("style", {})
        
        if not style:
            return styles
        
        if font := style.get("fontFamily"):
            styles["font-family"] = f"'{font}', sans-serif"
        if size := style.get("fontSize"):
            styles["font-size"] = f"{size}px"
        if weight := style.get("fontWeight"):
            styles["font-weight"] = str(weight)
        
        unit = style.get("lineHeightUnit", "AUTO")
        if unit == "PIXELS" and (lh := style.get("lineHeightPx")):
            styles["line-height"] = f"{lh}px"
        elif unit == "FONT_SIZE_%":
            styles["line-height"] = f"{style.get('lineHeightPercent', 100) / 100}"
        
        if (ls := style.get("letterSpacing", 0)) != 0:
            styles["letter-spacing"] = f"{ls}px"
        
        align_map = {"LEFT": "left", "CENTER": "center", "RIGHT": "right", "JUSTIFIED": "justify"}
        styles["text-align"] = align_map.get(style.get("textAlignHorizontal", "LEFT"), "left")
        
        # Text color
        fills = node.get("fills", [])
        if fills and fills[0].get("type") == "SOLID":
            if color := fills[0].get("color"):
                styles["color"] = rgba_to_hex(color)
        
        return styles
    
    def _generate_class_name(self, node: FigmaNode) -> str:
        """Generate BEM-style class name."""
        name = node.get("name", "element")
        node_id = node.get("id", "")
        
        class_name = sanitize_css_class(name)
        
        # Add ID suffix for duplicate-prone names
        duplicates = ["background", "rectangle", "group", "frame", "vector", "path", "layer", "text-field"]
        if any(d in class_name for d in duplicates):
            suffix = node_id.replace(":", "-").replace(";", "-")[-6:].lower()
            class_name = f"{class_name}-{suffix}"
        
        return f"{self.component_name}__{class_name}"
