"""Generate Tailwind CSS classes from Figma nodes.

This module generates Tailwind utility classes instead of custom SCSS,
providing an alternative styling approach for Tailwind-based projects.
"""

from typing import Dict, Any, List, Optional
from ..figma.types import FigmaNode
from ..utils.colors import rgba_to_hex


class TailwindGenerator:
    """Generates Tailwind utility classes for Angular components.
    
    Maps Figma design properties to Tailwind utility classes:
    - Colors → text-[#hex], bg-[#hex]
    - Spacing → p-[Xpx], m-[Xpx], gap-[Xpx]
    - Typography → text-[Xpx], font-[weight], leading-[X]
    - Layout → flex, flex-col, justify-X, items-X
    - Borders → rounded-[Xpx], border-[Xpx]
    - Shadows → shadow-[custom]
    """
    
    def __init__(self, component_name: str, responsive_mode: bool = False):
        """Initialize the Tailwind generator.
        
        Args:
            component_name: Name of the component
            responsive_mode: If True, use flexbox-based layouts
        """
        self.component_name = component_name
        self.responsive_mode = responsive_mode
        self.class_map: Dict[str, str] = {}  # Maps node ID to Tailwind classes
    
    def generate_classes(self, node: FigmaNode) -> Dict[str, str]:
        """Generate Tailwind class strings for all nodes.
        
        Returns:
            Dict mapping node names/IDs to Tailwind class strings
        """
        self.class_map = {}
        self._collect_node_classes(node, is_root=True)
        return self.class_map
    
    def _collect_node_classes(
        self, 
        node: FigmaNode, 
        parent: FigmaNode = None,
        is_root: bool = False
    ) -> None:
        """Recursively collect Tailwind classes for each node."""
        node_name = self._get_class_key(node)
        classes = self._generate_node_classes(node, parent, is_root)
        
        if classes:
            self.class_map[node_name] = " ".join(classes)
        
        # Process children
        for child in node.get("children", []):
            self._collect_node_classes(child, parent=node, is_root=False)
    
    def _generate_node_classes(
        self, 
        node: FigmaNode,
        parent: FigmaNode = None,
        is_root: bool = False
    ) -> List[str]:
        """Generate Tailwind classes for a single node."""
        classes = []
        
        # Layout classes
        classes.extend(self._layout_classes(node, parent, is_root))
        
        # Sizing classes
        classes.extend(self._sizing_classes(node, is_root))
        
        # Background classes
        classes.extend(self._background_classes(node))
        
        # Border classes
        classes.extend(self._border_classes(node))
        
        # Typography classes (for text nodes)
        if node.get("type") == "TEXT":
            classes.extend(self._typography_classes(node))
        
        # Shadow classes
        classes.extend(self._shadow_classes(node))
        
        return classes
    
    def _layout_classes(
        self, 
        node: FigmaNode, 
        parent: FigmaNode = None,
        is_root: bool = False
    ) -> List[str]:
        """Generate layout-related Tailwind classes."""
        classes = []
        
        layout_mode = node.get("layoutMode", "NONE")
        
        if layout_mode == "HORIZONTAL":
            classes.append("flex")
            classes.append("flex-row")
        elif layout_mode == "VERTICAL":
            classes.append("flex")
            classes.append("flex-col")
        
        # Alignment
        primary = node.get("primaryAxisAlignItems", "MIN")
        counter = node.get("counterAxisAlignItems", "MIN")
        
        justify_map = {
            "MIN": "justify-start",
            "CENTER": "justify-center",
            "MAX": "justify-end",
            "SPACE_BETWEEN": "justify-between",
        }
        
        align_map = {
            "MIN": "items-start",
            "CENTER": "items-center",
            "MAX": "items-end",
            "STRETCH": "items-stretch",
        }
        
        if primary in justify_map and layout_mode != "NONE":
            classes.append(justify_map[primary])
        if counter in align_map and layout_mode != "NONE":
            classes.append(align_map[counter])
        
        # Gap/spacing
        spacing = node.get("itemSpacing", 0)
        if spacing > 0:
            classes.append(f"gap-[{spacing}px]")
        
        # Padding
        pt = node.get("paddingTop", 0)
        pr = node.get("paddingRight", 0)
        pb = node.get("paddingBottom", 0)
        pl = node.get("paddingLeft", 0)
        
        if pt == pr == pb == pl and pt > 0:
            classes.append(f"p-[{pt}px]")
        else:
            if pt > 0:
                classes.append(f"pt-[{pt}px]")
            if pr > 0:
                classes.append(f"pr-[{pr}px]")
            if pb > 0:
                classes.append(f"pb-[{pb}px]")
            if pl > 0:
                classes.append(f"pl-[{pl}px]")
        
        # Position for non-flex layouts
        if not self.responsive_mode and is_root:
            classes.append("relative")
        elif not self.responsive_mode and not layout_mode in ["HORIZONTAL", "VERTICAL"]:
            bounds = node.get("absoluteBoundingBox", {})
            if parent and bounds:
                parent_bounds = parent.get("absoluteBoundingBox", {})
                if parent_bounds:
                    x = bounds.get("x", 0) - parent_bounds.get("x", 0)
                    y = bounds.get("y", 0) - parent_bounds.get("y", 0)
                    classes.append("absolute")
                    classes.append(f"left-[{x}px]")
                    classes.append(f"top-[{y}px]")
        
        return classes
    
    def _sizing_classes(self, node: FigmaNode, is_root: bool = False) -> List[str]:
        """Generate sizing-related Tailwind classes."""
        classes = []
        bounds = node.get("absoluteBoundingBox", {})
        
        w = bounds.get("width", 0)
        h = bounds.get("height", 0)
        
        if is_root:
            classes.append("w-full")
            if w > 0:
                classes.append(f"max-w-[{w}px]")
            classes.append("mx-auto")
        else:
            sizing_mode = node.get("primaryAxisSizingMode", "AUTO")
            if sizing_mode == "FILL":
                classes.append("flex-1")
            elif w > 0:
                classes.append(f"w-[{w}px]")
            
            if h > 0:
                classes.append(f"h-[{h}px]")
        
        return classes
    
    def _background_classes(self, node: FigmaNode) -> List[str]:
        """Generate background-related Tailwind classes."""
        classes = []
        fills = node.get("fills", [])
        
        for fill in fills:
            if not fill.get("visible", True):
                continue
            
            fill_type = fill.get("type")
            
            if fill_type == "SOLID":
                color = fill.get("color", {})
                r = int(color.get("r", 0) * 255)
                g = int(color.get("g", 0) * 255)
                b = int(color.get("b", 0) * 255)
                a = fill.get("opacity", color.get("a", 1))
                
                if a < 1:
                    classes.append(f"bg-[rgba({r},{g},{b},{a:.2f})]")
                else:
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    classes.append(f"bg-[{hex_color}]")
                break  # Only first visible fill
            
            elif fill_type == "GRADIENT_LINEAR":
                # Tailwind gradient approximation
                stops = fill.get("gradientStops", [])
                if len(stops) >= 2:
                    start_color = stops[0].get("color", {})
                    end_color = stops[-1].get("color", {})
                    
                    start_hex = rgba_to_hex(start_color)
                    end_hex = rgba_to_hex(end_color)
                    
                    classes.append(f"bg-gradient-to-r")
                    classes.append(f"from-[{start_hex}]")
                    classes.append(f"to-[{end_hex}]")
                break
        
        return classes
    
    def _border_classes(self, node: FigmaNode) -> List[str]:
        """Generate border-related Tailwind classes."""
        classes = []
        
        # Border radius
        radius = node.get("cornerRadius", 0)
        if radius > 0:
            if radius >= 9999:
                classes.append("rounded-full")
            else:
                classes.append(f"rounded-[{radius}px]")
        
        # Strokes
        strokes = node.get("strokes", [])
        stroke_weight = node.get("strokeWeight", 0)
        
        if strokes and stroke_weight > 0:
            for stroke in strokes:
                if not stroke.get("visible", True):
                    continue
                if stroke.get("type") == "SOLID":
                    color = stroke.get("color", {})
                    hex_color = rgba_to_hex(color)
                    classes.append(f"border-[{stroke_weight}px]")
                    classes.append(f"border-[{hex_color}]")
                    break
        
        return classes
    
    def _typography_classes(self, node: FigmaNode) -> List[str]:
        """Generate typography-related Tailwind classes."""
        classes = []
        style = node.get("style", {})
        
        # Font size
        font_size = style.get("fontSize", 0)
        if font_size > 0:
            classes.append(f"text-[{font_size}px]")
        
        # Font weight
        weight = style.get("fontWeight", 400)
        weight_map = {
            100: "font-thin",
            200: "font-extralight",
            300: "font-light",
            400: "font-normal",
            500: "font-medium",
            600: "font-semibold",
            700: "font-bold",
            800: "font-extrabold",
            900: "font-black",
        }
        if weight in weight_map:
            classes.append(weight_map[weight])
        
        # Line height
        line_height = style.get("lineHeightPx", 0)
        if line_height > 0:
            classes.append(f"leading-[{line_height}px]")
        
        # Letter spacing
        letter_spacing = style.get("letterSpacing", 0)
        if letter_spacing != 0:
            classes.append(f"tracking-[{letter_spacing}px]")
        
        # Text color
        fills = node.get("fills", [])
        for fill in fills:
            if fill.get("type") == "SOLID" and fill.get("visible", True):
                color = fill.get("color", {})
                hex_color = rgba_to_hex(color)
                classes.append(f"text-[{hex_color}]")
                break
        
        # Text alignment
        align = style.get("textAlignHorizontal", "LEFT")
        align_map = {
            "LEFT": "text-left",
            "CENTER": "text-center",
            "RIGHT": "text-right",
            "JUSTIFIED": "text-justify",
        }
        if align in align_map:
            classes.append(align_map[align])
        
        return classes
    
    def _shadow_classes(self, node: FigmaNode) -> List[str]:
        """Generate shadow-related Tailwind classes."""
        classes = []
        effects = node.get("effects", [])
        
        for effect in effects:
            if not effect.get("visible", True):
                continue
            
            effect_type = effect.get("type")
            if effect_type == "DROP_SHADOW":
                color = effect.get("color", {})
                offset = effect.get("offset", {})
                radius = effect.get("radius", 0)
                
                x = offset.get("x", 0)
                y = offset.get("y", 0)
                hex_color = rgba_to_hex(color)
                
                # Use arbitrary shadow value
                classes.append(f"shadow-[{x}px_{y}px_{radius}px_{hex_color}]")
                break  # Only first shadow
        
        return classes
    
    def _get_class_key(self, node: FigmaNode) -> str:
        """Generate a key for the class map."""
        name = node.get("name", "element")
        # Convert to valid key
        key = name.lower().replace(" ", "-").replace("/", "-")
        return key
    
    def generate_inline_styles(self, node: FigmaNode) -> str:
        """Generate inline Tailwind class attribute for HTML.
        
        Returns a string like: class="flex flex-col gap-4 p-6 bg-white rounded-lg"
        """
        classes = self.generate_classes(node)
        root_key = self._get_class_key(node)
        return classes.get(root_key, "")
