"""Tests for extractors."""

import pytest
from src.extractors.tokens import TokenExtractor
from src.extractors.token_scss import TokenSCSSGenerator


class TestTokenExtractor:
    """Tests for design token extraction."""
    
    def test_extract_tokens_from_nodes(self, sample_figma_node):
        """Test token extraction from nodes."""
        extractor = TokenExtractor()
        tokens = extractor.extract_tokens({"1:23": sample_figma_node})
        
        assert "colors" in tokens
        assert "typography" in tokens
        assert "shadows" in tokens
    
    def test_extract_colors(self, sample_figma_node):
        """Test color extraction."""
        extractor = TokenExtractor()
        tokens = extractor.extract_tokens({"1:23": sample_figma_node})
        
        assert len(tokens["colors"]) > 0
    
    def test_extract_typography(self, sample_figma_node):
        """Test typography extraction from TEXT nodes."""
        extractor = TokenExtractor()
        tokens = extractor.extract_tokens({"1:23": sample_figma_node})
        
        assert len(tokens["typography"]) > 0
        
        # Check typography structure
        for key, style in tokens["typography"].items():
            assert "fontFamily" in style
            assert "fontSize" in style
    
    def test_extract_shadows(self, sample_figma_node):
        """Test shadow extraction from effects."""
        extractor = TokenExtractor()
        tokens = extractor.extract_tokens({"1:23": sample_figma_node})
        
        assert len(tokens["shadows"]) > 0


class TestTokenSCSSGenerator:
    """Tests for SCSS token generation."""
    
    def test_generate_scss_from_tokens(self, sample_design_tokens):
        """Test SCSS generation from design tokens."""
        gen = TokenSCSSGenerator()
        result = gen.generate_scss(sample_design_tokens)
        
        assert "$color-primary:" in result
        assert "$spacing-md:" in result
        assert "$radius-md:" in result
    
    def test_generate_scss_colors(self, sample_design_tokens):
        """Test color variable generation."""
        gen = TokenSCSSGenerator()
        result = gen.generate_scss(sample_design_tokens)
        
        assert "$color-primary: #3B82F6;" in result
        assert "$color-white: #FFFFFF;" in result
    
    def test_generate_scss_typography(self, sample_design_tokens):
        """Test typography variable generation."""
        gen = TokenSCSSGenerator()
        result = gen.generate_scss(sample_design_tokens)
        
        assert "$font-family-inter:" in result
    
    def test_generate_mixins(self, sample_design_tokens):
        """Test mixin generation."""
        gen = TokenSCSSGenerator()
        result = gen.generate_mixins(sample_design_tokens)
        
        assert "@mixin typography($style)" in result
        assert "@mixin shadow($level)" in result
