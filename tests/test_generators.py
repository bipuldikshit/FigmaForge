"""Tests for code generators."""

import pytest
from src.generators.html_generator import HTMLGenerator
from src.generators.typescript_generator import TypeScriptGenerator
from src.generators.scss_generator import SCSSComponentGenerator


class TestHTMLGenerator:
    """Tests for HTML template generation."""
    
    def test_generate_template_basic(self, sample_figma_node):
        """Test basic HTML template generation."""
        gen = HTMLGenerator("my-button")
        result = gen.generate_template(sample_figma_node)
        
        assert "AUTO-GEN-START" in result
        assert "AUTO-GEN-END" in result
        assert 'class="my-button"' in result
    
    def test_generate_template_contains_text(self, sample_figma_node):
        """Test that text content is included."""
        gen = HTMLGenerator("my-button")
        result = gen.generate_template(sample_figma_node)
        
        assert "Click Me" in result
    
    def test_generate_class_names_bem_style(self, sample_figma_node):
        """Test BEM-style class name generation."""
        gen = HTMLGenerator("my-button")
        result = gen.generate_template(sample_figma_node)
        
        assert "my-button__" in result


class TestTypeScriptGenerator:
    """Tests for TypeScript component generation."""
    
    def test_generate_component_structure(self, sample_figma_node):
        """Test basic component structure."""
        gen = TypeScriptGenerator("my-button")
        result = gen.generate_component(sample_figma_node)
        
        assert "import { Component, Input }" in result
        assert "@Component({" in result
        assert "selector: 'app-my-button'" in result
        assert "standalone: true" in result
        assert "export class MyButtonComponent" in result
    
    def test_generate_component_auto_gen_markers(self, sample_figma_node):
        """Test AUTO-GEN markers are present."""
        gen = TypeScriptGenerator("my-button")
        result = gen.generate_component(sample_figma_node)
        
        assert "AUTO-GEN-START" in result
        assert "AUTO-GEN-END" in result
    
    def test_generate_inputs_from_text(self, sample_figma_node):
        """Test @Input generation from TEXT nodes."""
        gen = TypeScriptGenerator("my-button")
        result = gen.generate_component(sample_figma_node)
        
        assert "@Input()" in result


class TestSCSSComponentGenerator:
    """Tests for SCSS component style generation."""
    
    def test_generate_scss_basic(self, sample_figma_node):
        """Test basic SCSS generation."""
        gen = SCSSComponentGenerator("my-button")
        result = gen.generate_scss(sample_figma_node)
        
        assert "AUTO-GEN-START" in result
        assert "AUTO-GEN-END" in result
        assert ".my-button {" in result
    
    def test_generate_scss_imports_tokens(self, sample_figma_node):
        """Test design tokens import."""
        gen = SCSSComponentGenerator("my-button")
        result = gen.generate_scss(sample_figma_node, import_tokens=True)
        
        assert "@import" in result
        assert "design-tokens" in result
    
    def test_generate_scss_no_tokens_import(self, sample_figma_node):
        """Test SCSS without tokens import."""
        gen = SCSSComponentGenerator("my-button")
        result = gen.generate_scss(sample_figma_node, import_tokens=False)
        
        assert "@import" not in result
    
    def test_generate_scss_background(self, sample_figma_node):
        """Test background extraction (supports gradients via background property)."""
        gen = SCSSComponentGenerator("my-button")
        result = gen.generate_scss(sample_figma_node)
        
        assert "background:" in result
    
    def test_generate_scss_border_radius(self, sample_figma_node):
        """Test border radius extraction."""
        gen = SCSSComponentGenerator("my-button")
        result = gen.generate_scss(sample_figma_node)
        
        assert "border-radius:" in result
