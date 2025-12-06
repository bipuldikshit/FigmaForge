"""Generate Angular TypeScript component files."""

from typing import Set, Dict, Any
from ..figma.types import FigmaNode


class TypeScriptGenerator:
    """Generates Angular standalone component TypeScript files."""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.selector = f"app-{component_name}"
        self.class_name = self._to_pascal_case(component_name) + "Component"
        self.inputs: Set[str] = set()
    
    def generate_component(self, node: FigmaNode) -> str:
        """Generate Angular component TypeScript code."""
        self._analyze_node_for_inputs(node)
        
        lines = [
            "import { Component, Input } from '@angular/core';",
            "import { CommonModule } from '@angular/common';",
            "",
            f"/** {self.class_name} - Generated from Figma */",
            "@Component({",
            f"  selector: '{self.selector}',",
            "  standalone: true,",
            "  imports: [CommonModule],",
            f"  templateUrl: './{self.component_name}.component.html',",
            f"  styleUrls: ['./{self.component_name}.component.scss']",
            "})",
            f"export class {self.class_name} {{",
            "  // ==================== AUTO-GEN-START ====================",
        ]
        
        if self.inputs:
            for input_name in sorted(self.inputs):
                input_type = self._infer_input_type(input_name)
                default_value = self._get_default_value(input_type)
                lines.append(f"  @Input() {input_name}: {input_type} = {default_value};")
        else:
            lines.append("  // No dynamic inputs detected")
        
        lines.extend([
            "  // ==================== AUTO-GEN-END ====================",
            "",
            "  constructor() {}",
            "}",
            ""
        ])
        
        return "\n".join(lines)
    
    def _analyze_node_for_inputs(self, node: FigmaNode) -> None:
        """Recursively analyze node to identify @Input properties."""
        node_type = node.get("type", "")
        node_name = node.get("name", "")
        
        if node_type == "TEXT":
            prop = self._to_property_name(node_name or "text")
            if len(prop) > 40:
                prop = self._abbreviate(prop)
            self.inputs.add(prop)
        
        elif node_type in ["RECTANGLE", "ELLIPSE", "VECTOR"]:
            fills = node.get("fills", [])
            has_image = any(f.get("type") == "IMAGE" for f in fills)
            
            if has_image or any(k in node_name.lower() for k in ["image", "icon", "logo"]):
                prop = self._to_property_name(node_name or "image")
                if not prop.lower().endswith(("url", "src")):
                    prop += "Url"
                if len(prop) > 40:
                    prop = self._abbreviate(prop)
                self.inputs.add(prop)
        
        if any(k in node_name.lower() for k in ["color", "accent", "theme"]):
            prop = self._to_property_name(node_name or "color")
            if not prop.lower().endswith("color"):
                prop += "Color"
            if len(prop) > 40:
                prop = self._abbreviate(prop)
            self.inputs.add(prop)
        
        for child in node.get("children", []):
            if isinstance(child, dict):
                self._analyze_node_for_inputs(child)
    
    def _abbreviate(self, name: str) -> str:
        """Abbreviate long property names."""
        abbrevs = {
            "description": "desc", "information": "info", "message": "msg",
            "template": "tmpl", "navigation": "nav", "button": "btn",
            "image": "img", "configuration": "config", "certificate": "cert",
            "customer": "cust", "corporate": "corp", "instructions": "instr",
            "document": "doc", "application": "app"
        }
        
        words = []
        current = ""
        for c in name:
            if c.isupper() and current:
                words.append(current.lower())
                current = c
            else:
                current += c
        if current:
            words.append(current.lower())
        
        abbreviated = [abbrevs.get(w, w) for w in words]
        
        if not abbreviated:
            return name[:40]
        
        result = abbreviated[0]
        for w in abbreviated[1:]:
            result += w.capitalize()
        
        return result[:40] if len(result) > 40 else result
    
    def _infer_input_type(self, input_name: str) -> str:
        """Infer TypeScript type from input name."""
        lower = input_name.lower()
        
        if any(k in lower for k in ["url", "src", "image", "icon", "color", "theme"]):
            return "string"
        if any(k in lower for k in ["count", "number", "amount", "total"]):
            return "number"
        if lower.startswith(("is", "has", "show")) or any(k in lower for k in ["enabled", "visible", "active", "disabled"]):
            return "boolean"
        return "string"
    
    def _get_default_value(self, type_name: str) -> str:
        """Get default value for TypeScript type."""
        return {"string": "''", "number": "0", "boolean": "false", "any[]": "[]"}.get(type_name, "''")
    
    def _to_property_name(self, text: str) -> str:
        """Convert text to camelCase property name."""
        for char in "<>/\\()[]{}:;,.!?":
            text = text.replace(char, " ")
        text = text.replace("&", "and").replace("+", "plus").replace("=", "equals")
        text = text.replace("-", " ").replace("_", " ")
        
        stop_words = {"the", "a", "an", "to", "for", "of", "in", "on", "at"}
        words = [w for w in text.split() if w and w.lower() not in stop_words]
        
        if not words:
            return "text"
        
        prop = words[0].lower()
        for w in words[1:]:
            if w:
                prop += w[0].upper() + w[1:].lower()
        
        if not prop or not prop[0].isalpha():
            prop = "value" + prop.capitalize()
        
        return "".join(c for c in prop if c.isalnum()) or "text"
    
    def _to_pascal_case(self, text: str) -> str:
        """Convert kebab-case to PascalCase."""
        return "".join(w.capitalize() for w in text.replace("-", " ").replace("_", " ").split() if w)
