"""Generate SCSS variable files from design tokens."""

from typing import Dict, Any
from ..figma.types import DesignTokens
from ..utils.console import console


class SCSSGenerator:
    """Converts design tokens to SCSS variables and mixins."""
    
    def generate_scss(self, tokens: DesignTokens) -> str:
        """Generate SCSS variables from design tokens."""
        lines = [
            "// Design Tokens - Generated from Figma",
            "// DO NOT EDIT MANUALLY",
            "",
            "// Colors",
        ]
        
        for name, value in sorted(tokens.get("colors", {}).items()):
            lines.append(f"$color-{name}: {value};")
        
        lines.extend(["", "// Typography"])
        
        for font in tokens.get("fontFamilies", []):
            var_name = self._sanitize_font_name(font)
            lines.append(f"$font-family-{var_name}: '{font}', sans-serif;")
        
        for style_name, props in tokens.get("typography", {}).items():
            safe_name = self._sanitize_name(style_name)
            lines.append("")
            if "fontSize" in props:
                lines.append(f"$font-size-{safe_name}: {props['fontSize']};")
            if "fontWeight" in props:
                lines.append(f"$font-weight-{safe_name}: {props['fontWeight']};")
            if "lineHeight" in props:
                lines.append(f"$line-height-{safe_name}: {props['lineHeight']};")
        
        lines.extend(["", "// Spacing"])
        for name, value in sorted(tokens.get("spacing", {}).items()):
            lines.append(f"$spacing-{name}: {value};")
        
        lines.extend(["", "// Border Radii"])
        for name, value in sorted(tokens.get("radii", {}).items()):
            lines.append(f"$radius-{name}: {value};")
        
        lines.extend(["", "// Shadows"])
        for name, value in sorted(tokens.get("shadows", {}).items()):
            lines.append(f"$shadow-{name}: {value};")
        
        lines.append("")
        return "\n".join(lines)
    
    def save_scss(self, tokens: DesignTokens, output_path: str) -> None:
        """Generate and save SCSS file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_scss(tokens))
        console.print(f"[green]✓ Saved: {output_path}[/green]")
    
    def generate_mixins(self, tokens: DesignTokens) -> str:
        """Generate SCSS mixins for typography and shadows."""
        lines = [
            "// SCSS Mixins - Generated from Figma",
            "",
            "@mixin typography($style) {",
        ]
        
        for style_name in tokens.get("typography", {}):
            safe_name = self._sanitize_name(style_name)
            lines.extend([
                f"  @if $style == '{safe_name}' {{",
                f"    font-size: $font-size-{safe_name};",
                f"    font-weight: $font-weight-{safe_name};",
                f"    line-height: $line-height-{safe_name};",
                "  }"
            ])
        
        lines.extend(["}", "", "@mixin shadow($level) {"])
        
        for shadow_name in tokens.get("shadows", {}):
            lines.extend([
                f"  @if $level == '{shadow_name}' {{",
                f"    box-shadow: $shadow-{shadow_name};",
                "  }"
            ])
        
        lines.extend(["}", ""])
        return "\n".join(lines)
    
    @staticmethod
    def _sanitize_name(name: str) -> str:
        name = name.lower().replace(" ", "-").replace("_", "-")
        name = "".join(c for c in name if c.isalnum() or c == "-")
        return name.strip("-")
    
    @staticmethod
    def _sanitize_font_name(font_name: str) -> str:
        return font_name.replace("'", "").replace('"', "").replace(" ", "-").lower()
