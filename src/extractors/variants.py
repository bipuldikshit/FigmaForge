"""Extract and process Figma component variants.

This module handles detection and extraction of Figma Component Sets
(variants) and generates appropriate Angular @Input() properties.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from ..figma.types import FigmaNode


@dataclass
class VariantProperty:
    """Represents a variant property definition."""
    name: str
    options: List[str]
    default_value: str


@dataclass
class ComponentVariant:
    """Represents a single variant of a component."""
    name: str
    node_id: str
    properties: Dict[str, str]  # property_name -> value
    node: FigmaNode


class VariantExtractor:
    """Extracts variant information from Figma Component Sets.
    
    Figma Component Sets structure:
    - type: COMPONENT_SET
    - children: Array of COMPONENT nodes (each is a variant)
    - componentPropertyDefinitions: Defines variant properties
    
    Each variant child has a name like "Size=Large, State=Hover"
    which encodes its property values.
    """
    
    def is_component_set(self, node: FigmaNode) -> bool:
        """Check if a node is a Component Set (variants container)."""
        return node.get("type") == "COMPONENT_SET"
    
    def extract_variants(self, node: FigmaNode) -> Optional[Dict[str, Any]]:
        """Extract variant information from a Component Set.
        
        Returns:
            Dict with:
                - properties: List[VariantProperty] - available variant properties
                - variants: List[ComponentVariant] - all variants
                - default_variant: ComponentVariant - the default variant
            
            Returns None if node is not a Component Set.
        """
        if not self.is_component_set(node):
            return None
        
        # Extract property definitions
        prop_definitions = node.get("componentPropertyDefinitions", {})
        properties = self._extract_property_definitions(prop_definitions)
        
        # Extract all variants
        variants = self._extract_variants(node, properties)
        
        # Find default variant (first child or top-left most)
        default_variant = variants[0] if variants else None
        
        return {
            "properties": properties,
            "variants": variants,
            "default_variant": default_variant,
        }
    
    def _extract_property_definitions(
        self, 
        prop_definitions: Dict[str, Any]
    ) -> List[VariantProperty]:
        """Extract variant property definitions."""
        properties = []
        
        for prop_name, prop_def in prop_definitions.items():
            prop_type = prop_def.get("type")
            
            if prop_type == "VARIANT":
                options = prop_def.get("variantOptions", [])
                default_value = prop_def.get("defaultValue", options[0] if options else "")
                
                properties.append(VariantProperty(
                    name=prop_name,
                    options=options,
                    default_value=default_value
                ))
        
        return properties
    
    def _extract_variants(
        self, 
        node: FigmaNode,
        properties: List[VariantProperty]
    ) -> List[ComponentVariant]:
        """Extract all variants from a Component Set."""
        variants = []
        
        for child in node.get("children", []):
            if child.get("type") == "COMPONENT":
                # Parse variant name like "Size=Large, State=Hover"
                variant_name = child.get("name", "")
                prop_values = self._parse_variant_name(variant_name)
                
                variants.append(ComponentVariant(
                    name=variant_name,
                    node_id=child.get("id", ""),
                    properties=prop_values,
                    node=child
                ))
        
        return variants
    
    def _parse_variant_name(self, name: str) -> Dict[str, str]:
        """Parse variant name string into property-value pairs.
        
        Example: "Size=Large, State=Hover" -> {"Size": "Large", "State": "Hover"}
        """
        props = {}
        
        if not name:
            return props
        
        # Split by comma and parse each pair
        pairs = name.split(",")
        for pair in pairs:
            pair = pair.strip()
            if "=" in pair:
                key, value = pair.split("=", 1)
                props[key.strip()] = value.strip()
        
        return props
    
    def generate_angular_inputs(
        self, 
        variant_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate Angular @Input() property definitions.
        
        Returns:
            List of input definitions, each with:
                - name: Property name (camelCase)
                - type: TypeScript type (union of options)
                - default: Default value
                - options: List of possible values
        """
        inputs = []
        
        for prop in variant_info.get("properties", []):
            # Convert to camelCase for Angular
            input_name = self._to_camel_case(prop.name)
            
            # Create TypeScript union type
            if prop.options:
                ts_type = " | ".join(f"'{opt}'" for opt in prop.options)
            else:
                ts_type = "string"
            
            inputs.append({
                "name": input_name,
                "original_name": prop.name,
                "type": ts_type,
                "default": prop.default_value,
                "options": prop.options,
            })
        
        return inputs
    
    def _to_camel_case(self, name: str) -> str:
        """Convert property name to camelCase."""
        # Handle common separators
        words = name.replace("-", " ").replace("_", " ").split()
        if not words:
            return name.lower()
        
        # First word lowercase, rest title case
        result = words[0].lower()
        for word in words[1:]:
            result += word.title()
        
        return result
    
    def generate_variant_scss(
        self,
        component_name: str,
        variant_info: Dict[str, Any]
    ) -> str:
        """Generate SCSS with variant-specific styles using host-context.
        
        Generates styles like:
        :host-context(.button--size-large) { ... }
        :host-context(.button--state-hover) { ... }
        """
        lines = [
            "",
            "// ==================== VARIANT STYLES ====================",
            "// Use Angular's [class] binding to apply variant classes",
            "",
        ]
        
        for prop in variant_info.get("properties", []):
            prop_name_kebab = prop.name.lower().replace(" ", "-")
            
            for option in prop.options:
                option_kebab = option.lower().replace(" ", "-")
                modifier = f"{component_name}--{prop_name_kebab}-{option_kebab}"
                
                lines.append(f":host-context(.{modifier}) {{")
                lines.append(f"  // Styles for {prop.name}={option}")
                lines.append("}")
                lines.append("")
        
        return "\n".join(lines)
    
    def find_variant_by_props(
        self,
        variant_info: Dict[str, Any],
        props: Dict[str, str]
    ) -> Optional[ComponentVariant]:
        """Find a specific variant by property values."""
        for variant in variant_info.get("variants", []):
            if all(variant.properties.get(k) == v for k, v in props.items()):
                return variant
        return None
