"""Extract interaction states from Figma component variants.

Detects variant properties that represent interaction states
(hover, focus, pressed, disabled) and generates corresponding
CSS pseudo-class styles.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from .variants import VariantExtractor, VariantProperty, ComponentVariant


# Keyword mapping for state detection
STATE_KEYWORDS = {
    "hover": [":hover"],
    "hovered": [":hover"],
    "focus": [":focus", ":focus-visible"],
    "focused": [":focus", ":focus-visible"],
    "active": [":active"],
    "pressed": [":active"],
    "disabled": [":disabled", "[disabled]"],
    "selected": [".selected", '[aria-selected="true"]'],
    "checked": [":checked"],
    "error": [".error", '[aria-invalid="true"]'],
    "loading": [".loading"],
    "default": [],  # No pseudo-class needed
    "normal": [],
    "rest": [],
}


@dataclass
class InteractionState:
    """Represents an interaction state with its CSS selectors."""
    name: str
    css_selectors: List[str]
    variant: ComponentVariant
    property_name: str


class InteractionStatesExtractor:
    """Extracts interaction states from Figma component variants.
    
    Detects variant properties like:
    - State=Hover, State=Focus, State=Pressed, State=Disabled
    - Interaction=Hover, Interaction=Active
    
    And generates CSS pseudo-class rules.
    """
    
    STATE_PROPERTY_NAMES = ["state", "states", "interaction", "status"]
    
    def __init__(self, variant_extractor: Optional[VariantExtractor] = None):
        self.variant_extractor = variant_extractor or VariantExtractor()
    
    def extract_states(self, variant_info: Dict[str, Any]) -> List[InteractionState]:
        """Extract interaction states from variant info.
        
        Args:
            variant_info: Output from VariantExtractor.extract_variants()
            
        Returns:
            List of InteractionState objects
        """
        if not variant_info:
            return []
        
        states = []
        properties = variant_info.get("properties", [])
        variants = variant_info.get("variants", [])
        
        # Find state-related properties
        state_props = self._find_state_properties(properties)
        
        if not state_props:
            return []
        
        # Extract states for each variant
        for variant in variants:
            for prop in state_props:
                state_value = variant.properties.get(prop.name, "").lower()
                
                if state_value and state_value in STATE_KEYWORDS:
                    css_selectors = STATE_KEYWORDS[state_value]
                    if css_selectors:  # Skip default/normal states
                        states.append(InteractionState(
                            name=state_value,
                            css_selectors=css_selectors,
                            variant=variant,
                            property_name=prop.name
                        ))
        
        return states
    
    def _find_state_properties(
        self, 
        properties: List[VariantProperty]
    ) -> List[VariantProperty]:
        """Find properties that represent interaction states."""
        state_props = []
        
        for prop in properties:
            prop_name_lower = prop.name.lower()
            
            # Check if property name indicates a state
            if any(keyword in prop_name_lower for keyword in self.STATE_PROPERTY_NAMES):
                state_props.append(prop)
                continue
            
            # Check if property options contain state keywords
            option_states = [opt.lower() for opt in prop.options]
            if any(state in STATE_KEYWORDS for state in option_states):
                state_props.append(prop)
        
        return state_props
    
    def generate_scss_states(
        self, 
        component_name: str,
        states: List[InteractionState],
        base_styles: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate SCSS with pseudo-class rules for interaction states.
        
        Args:
            component_name: Name of the component
            states: List of InteractionState objects
            base_styles: Optional base styles to diff against
            
        Returns:
            SCSS string with pseudo-class rules
        """
        if not states:
            return ""
        
        lines = [
            "",
            "// ==================== INTERACTION STATES ====================",
            "// Auto-generated from Figma variant states",
            "",
        ]
        
        # Group states by their CSS selector
        selector_groups: Dict[str, List[InteractionState]] = {}
        for state in states:
            for selector in state.css_selectors:
                if selector not in selector_groups:
                    selector_groups[selector] = []
                selector_groups[selector].append(state)
        
        # Generate CSS rules
        for selector, state_list in selector_groups.items():
            state_names = ", ".join(set(s.name for s in state_list))
            
            if selector.startswith(":"):
                # Pseudo-class
                lines.append(f"&{selector} {{")
            elif selector.startswith("["):
                # Attribute selector
                lines.append(f"&{selector} {{")
            else:
                # Class selector
                lines.append(f"&{selector} {{")
            
            lines.append(f"  // {state_names} state styles")
            lines.append("  // TODO: Add variant-specific styles here")
            lines.append("}")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_css_states(
        self, 
        component_name: str,
        states: List[InteractionState]
    ) -> str:
        """Generate plain CSS with pseudo-class rules."""
        if not states:
            return ""
        
        lines = [
            "",
            "/* Interaction states from Figma variants */",
            "",
        ]
        
        selector_set = set()
        for state in states:
            for selector in state.css_selectors:
                selector_set.add(selector)
        
        for selector in sorted(selector_set):
            if selector.startswith(":"):
                lines.append(f".{component_name}{selector} {{")
            else:
                lines.append(f".{component_name}{selector} {{")
            lines.append("  /* Add variant-specific styles */")
            lines.append("}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_state_input_definitions(
        self, 
        states: List[InteractionState]
    ) -> List[Dict[str, Any]]:
        """Generate Angular @Input() definitions for state management.
        
        For cases where CSS pseudo-classes aren't sufficient,
        generate inputs for programmatic state control.
        """
        state_names = set()
        inputs = []
        
        for state in states:
            if state.name not in state_names and state.name not in ["hover", "focus", "active"]:
                # States like 'disabled', 'selected', 'error' need programmatic control
                state_names.add(state.name)
                inputs.append({
                    "name": f"is{state.name.capitalize()}",
                    "type": "boolean",
                    "default": "false",
                    "description": f"Set {state.name} state programmatically"
                })
        
        return inputs
