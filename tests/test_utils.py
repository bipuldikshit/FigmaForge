"""Tests for utility modules."""

import pytest
from src.utils.colors import rgba_to_hex, rgba_to_css, get_semantic_color_name
from src.utils.css import effect_to_shadow, sanitize_css_class, to_camel_case, to_pascal_case


class TestColorUtils:
    """Tests for color conversion functions."""
    
    def test_rgba_to_hex_opaque(self):
        """Test RGB to hex conversion without alpha."""
        color = {"r": 1.0, "g": 0.0, "b": 0.0, "a": 1.0}
        assert rgba_to_hex(color) == "#FF0000"
    
    def test_rgba_to_hex_with_alpha(self):
        """Test RGBA to hex conversion with alpha."""
        color = {"r": 0.0, "g": 0.0, "b": 1.0, "a": 0.5}
        result = rgba_to_hex(color)
        assert result.startswith("#0000FF")
        assert len(result) == 9  # Includes alpha
    
    def test_rgba_to_hex_partial_values(self):
        """Test conversion with partial color values."""
        color = {"r": 0.5, "g": 0.5, "b": 0.5}
        result = rgba_to_hex(color)
        assert result.startswith("#")
        assert len(result) == 7  # No alpha when a=1.0 (default)
    
    def test_rgba_to_css(self):
        """Test conversion to CSS rgba() string."""
        color = {"r": 1.0, "g": 0.5, "b": 0.0, "a": 1.0}
        result = rgba_to_css(color, 0.5)
        assert "rgba(255, 127, 0," in result
    
    def test_get_semantic_color_name_known(self):
        """Test semantic name lookup for known colors."""
        assert get_semantic_color_name("#FFFFFF") == "white"
        assert get_semantic_color_name("#000000") == "black"
        assert get_semantic_color_name("#FF0000") == "red"
    
    def test_get_semantic_color_name_unknown(self):
        """Test semantic name lookup for unknown colors."""
        assert get_semantic_color_name("#123456") == ""


class TestCSSUtils:
    """Tests for CSS utility functions."""
    
    def test_effect_to_shadow_drop(self):
        """Test drop shadow conversion."""
        effect = {
            "type": "DROP_SHADOW",
            "offset": {"x": 0, "y": 4},
            "radius": 6,
            "spread": 0,
            "color": {"r": 0, "g": 0, "b": 0, "a": 0.1}
        }
        result = effect_to_shadow(effect)
        assert "0px 4px 6px 0px rgba(0, 0, 0, 0.1)" in result
        assert "inset" not in result
    
    def test_effect_to_shadow_inner(self):
        """Test inner shadow conversion."""
        effect = {
            "type": "INNER_SHADOW",
            "offset": {"x": 2, "y": 2},
            "radius": 4,
            "spread": 0,
            "color": {"r": 0, "g": 0, "b": 0, "a": 0.2}
        }
        result = effect_to_shadow(effect)
        assert result.startswith("inset")
    
    def test_sanitize_css_class_basic(self):
        """Test basic class name sanitization."""
        assert sanitize_css_class("My Button") == "my-button"
        assert sanitize_css_class("Primary/Secondary") == "primary-secondary"
        assert sanitize_css_class("item_with_underscores") == "item-with-underscores"
    
    def test_sanitize_css_class_consecutive_dashes(self):
        """Test removal of consecutive dashes."""
        assert sanitize_css_class("my--button") == "my-button"
        assert sanitize_css_class("a - b - c") == "a-b-c"
    
    def test_sanitize_css_class_starts_with_number(self):
        """Test handling of classes starting with numbers."""
        assert sanitize_css_class("123button").startswith("c-")
    
    def test_to_camel_case(self):
        """Test conversion to camelCase."""
        assert to_camel_case("button-label") == "buttonLabel"
        assert to_camel_case("primary_button_text") == "primaryButtonText"
        assert to_camel_case("My Button Label") == "myButtonLabel"
    
    def test_to_camel_case_with_stop_words(self):
        """Test that stop words are filtered."""
        result = to_camel_case("label for the button")
        assert "the" not in result.lower()
        assert "for" not in result.lower()
    
    def test_to_pascal_case(self):
        """Test conversion to PascalCase."""
        assert to_pascal_case("my-component") == "MyComponent"
        assert to_pascal_case("primary_button") == "PrimaryButton"
