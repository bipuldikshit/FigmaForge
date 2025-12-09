"""Pytest configuration and shared fixtures for FigmaForge tests."""

import pytest
from typing import Dict, Any


@pytest.fixture
def sample_figma_node() -> Dict[str, Any]:
    """Sample Figma node for testing generators."""
    return {
        "id": "1:23",
        "name": "Primary Button",
        "type": "COMPONENT",
        "absoluteBoundingBox": {"x": 0, "y": 0, "width": 200, "height": 48},
        "fills": [
            {
                "type": "SOLID",
                "visible": True,
                "color": {"r": 0.231, "g": 0.510, "b": 0.965, "a": 1.0}
            }
        ],
        "strokes": [],
        "cornerRadius": 8,
        "effects": [
            {
                "type": "DROP_SHADOW",
                "visible": True,
                "offset": {"x": 0, "y": 4},
                "radius": 6,
                "spread": 0,
                "color": {"r": 0, "g": 0, "b": 0, "a": 0.1}
            }
        ],
        "children": [
            {
                "id": "1:24",
                "name": "Button Label",
                "type": "TEXT",
                "characters": "Click Me",
                "absoluteBoundingBox": {"x": 24, "y": 12, "width": 152, "height": 24},
                "fills": [
                    {
                        "type": "SOLID",
                        "visible": True,
                        "color": {"r": 1, "g": 1, "b": 1, "a": 1}
                    }
                ],
                "style": {
                    "fontFamily": "Inter",
                    "fontSize": 16,
                    "fontWeight": 500,
                    "lineHeightPx": 24,
                    "letterSpacing": 0
                }
            }
        ]
    }


@pytest.fixture
def sample_figma_file() -> Dict[str, Any]:
    """Sample Figma file response."""
    return {
        "name": "Test Design System",
        "lastModified": "2024-01-15T10:30:00Z",
        "version": "123456789",
        "document": {
            "id": "0:0",
            "name": "Document",
            "type": "DOCUMENT",
            "children": [
                {
                    "id": "0:1",
                    "name": "Page 1",
                    "type": "CANVAS",
                    "children": []
                }
            ]
        },
        "components": {},
        "styles": {}
    }


@pytest.fixture
def sample_design_tokens() -> Dict[str, Any]:
    """Sample design tokens for testing."""
    return {
        "colors": {
            "primary": "#3B82F6",
            "white": "#FFFFFF",
            "black": "#000000"
        },
        "typography": {
            "Inter-16-500": {
                "fontFamily": "Inter",
                "fontSize": "16px",
                "fontWeight": 500,
                "lineHeight": "24px",
                "letterSpacing": "0px"
            }
        },
        "spacing": {
            "sm": "8px",
            "md": "16px",
            "lg": "24px"
        },
        "radii": {
            "sm": "4px",
            "md": "8px"
        },
        "shadows": {
            "md": "0px 4px 6px 0px rgba(0, 0, 0, 0.1)"
        },
        "fontFamilies": ["Inter"]
    }
