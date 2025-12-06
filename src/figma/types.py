"""Type definitions for Figma data structures."""

from typing import TypedDict, Literal, Optional, List, Dict, Any


# Layout Types
LayoutMode = Literal["NONE", "HORIZONTAL", "VERTICAL"]
LayoutAlign = Literal["MIN", "CENTER", "MAX", "STRETCH", "INHERIT"]
ConstraintType = Literal["MIN", "CENTER", "MAX", "STRETCH", "SCALE"]

# Node Types
NodeType = Literal[
    "DOCUMENT", "CANVAS", "FRAME", "GROUP", "VECTOR", "BOOLEAN_OPERATION",
    "STAR", "LINE", "ELLIPSE", "REGULAR_POLYGON", "RECTANGLE", "TEXT",
    "SLICE", "COMPONENT", "COMPONENT_SET", "INSTANCE", "STICKY", "SHAPE_WITH_TEXT"
]

# Paint Types
PaintType = Literal["SOLID", "GRADIENT_LINEAR", "GRADIENT_RADIAL", "GRADIENT_ANGULAR", "GRADIENT_DIAMOND", "IMAGE", "EMOJI"]
BlendMode = Literal["NORMAL", "DARKEN", "MULTIPLY", "COLOR_BURN", "LIGHTEN", "SCREEN", "COLOR_DODGE", "OVERLAY", "SOFT_LIGHT", "HARD_LIGHT"]


class Color(TypedDict):
    """RGBA Color definition."""
    r: float  # 0-1
    g: float  # 0-1
    b: float  # 0-1
    a: float  # 0-1


class Paint(TypedDict, total=False):
    """Paint/fill definition."""
    type: PaintType
    visible: bool
    opacity: float
    color: Color
    blendMode: BlendMode


class Effect(TypedDict, total=False):
    """Visual effect (shadow, blur, etc.)."""
    type: Literal["DROP_SHADOW", "INNER_SHADOW", "LAYER_BLUR", "BACKGROUND_BLUR"]
    visible: bool
    radius: float
    color: Color
    offset: Dict[str, float]  # x, y
    spread: float


class LayoutConstraint(TypedDict):
    """Layout constraints for responsive behavior."""
    vertical: ConstraintType
    horizontal: ConstraintType


class Rectangle(TypedDict):
    """Bounding rectangle."""
    x: float
    y: float
    width: float
    height: float


class TypeStyle(TypedDict, total=False):
    """Typography style."""
    fontFamily: str
    fontPostScriptName: str
    fontWeight: int
    fontSize: float
    textAlignHorizontal: Literal["LEFT", "CENTER", "RIGHT", "JUSTIFIED"]
    textAlignVertical: Literal["TOP", "CENTER", "BOTTOM"]
    letterSpacing: float
    lineHeightPx: float
    lineHeightPercent: float
    lineHeightUnit: Literal["PIXELS", "FONT_SIZE_%", "INTRINSIC_%"]


class ExportSetting(TypedDict):
    """Export settings for assets."""
    suffix: str
    format: Literal["JPG", "PNG", "SVG", "PDF"]
    constraint: Dict[str, Any]


class FigmaNode(TypedDict, total=False):
    """Base Figma node structure."""
    id: str
    name: str
    type: NodeType
    visible: bool
    locked: bool
    
    # Layout properties
    absoluteBoundingBox: Rectangle
    absoluteRenderBounds: Rectangle
    constraints: LayoutConstraint
    layoutMode: LayoutMode
    layoutAlign: LayoutAlign
    primaryAxisAlignItems: LayoutAlign
    counterAxisAlignItems: LayoutAlign
    primaryAxisSizingMode: Literal["FIXED", "AUTO"]
    counterAxisSizingMode: Literal["FIXED", "AUTO"]
    paddingLeft: float
    paddingRight: float
    paddingTop: float
    paddingBottom: float
    itemSpacing: float
    counterAxisSpacing: float
    layoutGrow: float
    
    # Style properties
    fills: List[Paint]
    strokes: List[Paint]
    strokeWeight: float
    strokeAlign: Literal["INSIDE", "OUTSIDE", "CENTER"]
    cornerRadius: float
    rectangleCornerRadii: List[float]  # [topLeft, topRight, bottomRight, bottomLeft]
    effects: List[Effect]
    opacity: float
    blendMode: BlendMode
    
    # Text properties
    characters: str
    style: TypeStyle
    
    # Export
    exportSettings: List[ExportSetting]
    
    # Hierarchy
    children: List['FigmaNode']
    
    # Additional metadata
    componentId: Optional[str]
    componentProperties: Optional[Dict[str, Any]]


class FigmaComponent(TypedDict):
    """Normalized component structure for code generation."""
    id: str
    name: str
    node: FigmaNode
    tokens: Dict[str, Any]
    assets: List[str]


class FigmaFile(TypedDict):
    """Complete Figma file structure."""
    name: str
    lastModified: str
    thumbnailUrl: str
    version: str
    document: FigmaNode
    components: Dict[str, Any]
    styles: Dict[str, Any]


class DesignTokens(TypedDict, total=False):
    """Extracted design tokens."""
    colors: Dict[str, str]
    typography: Dict[str, Dict[str, Any]]
    spacing: Dict[str, str]
    radii: Dict[str, str]
    shadows: Dict[str, str]
    fontFamilies: List[str]
