"""Extract and convert Figma Variables to design tokens.

The Figma Variables API provides access to design tokens (colors, numbers, 
strings, booleans) defined in Figma files, including multi-mode support
for theming (light/dark modes, breakpoints, etc.).
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from ..utils.colors import rgba_to_hex


@dataclass
class FigmaVariable:
    """Represents a Figma variable."""
    id: str
    name: str
    key: str
    variable_type: str  # COLOR, FLOAT, STRING, BOOLEAN
    values_by_mode: Dict[str, Any]
    collection_id: str
    resolved_type: str
    description: str = ""


@dataclass  
class VariableCollection:
    """Represents a collection of variables (e.g., 'colors', 'spacing')."""
    id: str
    name: str
    key: str
    modes: List[Dict[str, str]]  # [{"id": "mode1", "name": "Light"}, ...]
    default_mode_id: str
    variable_ids: List[str]


class FigmaVariablesExtractor:
    """Extracts design tokens from Figma Variables API response.
    
    Converts Figma variables to:
    - CSS custom properties (--var-name: value)
    - SCSS variables ($var-name: value)
    - JSON design tokens
    """
    
    def __init__(self):
        self.variables: Dict[str, FigmaVariable] = {}
        self.collections: Dict[str, VariableCollection] = {}
    
    def extract(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract variables and collections from API response.
        
        Args:
            api_response: Response from FigmaClient.get_local_variables()
            
        Returns:
            Dict with 'variables', 'collections', and 'tokens' keys
        """
        raw_variables = api_response.get("variables", {})
        raw_collections = api_response.get("variableCollections", {})
        
        # Parse collections
        for coll_id, coll_data in raw_collections.items():
            self.collections[coll_id] = VariableCollection(
                id=coll_id,
                name=coll_data.get("name", ""),
                key=coll_data.get("key", ""),
                modes=coll_data.get("modes", []),
                default_mode_id=coll_data.get("defaultModeId", ""),
                variable_ids=coll_data.get("variableIds", [])
            )
        
        # Parse variables
        for var_id, var_data in raw_variables.items():
            self.variables[var_id] = FigmaVariable(
                id=var_id,
                name=var_data.get("name", ""),
                key=var_data.get("key", ""),
                variable_type=var_data.get("resolvedType", ""),
                values_by_mode=var_data.get("valuesByMode", {}),
                collection_id=var_data.get("variableCollectionId", ""),
                resolved_type=var_data.get("resolvedType", ""),
                description=var_data.get("description", "")
            )
        
        # Generate tokens
        tokens = self._generate_tokens()
        
        return {
            "variables": self.variables,
            "collections": self.collections,
            "tokens": tokens
        }
    
    def _generate_tokens(self) -> Dict[str, Dict[str, Any]]:
        """Generate design tokens grouped by collection and mode."""
        tokens = {}
        
        for coll_id, collection in self.collections.items():
            coll_name = self._to_token_name(collection.name)
            tokens[coll_name] = {
                "modes": {},
                "default_mode": None
            }
            
            # Get default mode name
            for mode in collection.modes:
                if mode.get("modeId") == collection.default_mode_id:
                    tokens[coll_name]["default_mode"] = mode.get("name", "default")
                    break
            
            # Process each mode
            for mode in collection.modes:
                mode_id = mode.get("modeId", "")
                mode_name = self._to_token_name(mode.get("name", "default"))
                tokens[coll_name]["modes"][mode_name] = {}
                
                # Get variables in this collection
                for var_id in collection.variable_ids:
                    var = self.variables.get(var_id)
                    if not var:
                        continue
                    
                    var_name = self._to_token_name(var.name)
                    value = var.values_by_mode.get(mode_id)
                    
                    if value is not None:
                        resolved_value = self._resolve_value(value, var.variable_type)
                        tokens[coll_name]["modes"][mode_name][var_name] = {
                            "value": resolved_value,
                            "type": var.variable_type.lower(),
                            "description": var.description
                        }
        
        return tokens
    
    def _resolve_value(self, value: Any, var_type: str) -> Any:
        """Resolve a variable value to its CSS-usable form."""
        if var_type == "COLOR" and isinstance(value, dict):
            r = int(value.get("r", 0) * 255)
            g = int(value.get("g", 0) * 255)
            b = int(value.get("b", 0) * 255)
            a = value.get("a", 1)
            
            if a < 1:
                return f"rgba({r}, {g}, {b}, {a:.2f})"
            return f"#{r:02x}{g:02x}{b:02x}"
        
        elif var_type == "FLOAT":
            return value
        
        elif var_type == "STRING":
            return str(value)
        
        elif var_type == "BOOLEAN":
            return bool(value)
        
        # Handle variable alias (reference to another variable)
        if isinstance(value, dict) and value.get("type") == "VARIABLE_ALIAS":
            aliased_id = value.get("id", "")
            aliased_var = self.variables.get(aliased_id)
            if aliased_var:
                return f"var(--{self._to_token_name(aliased_var.name)})"
        
        return value
    
    def _to_token_name(self, name: str) -> str:
        """Convert variable name to valid token name."""
        # Replace slashes with dashes, remove special chars
        result = name.replace("/", "-").replace(" ", "-").lower()
        # Remove leading numbers
        while result and result[0].isdigit():
            result = result[1:]
        return result or "token"
    
    def generate_scss(self, tokens: Dict[str, Any], mode: str = None) -> str:
        """Generate SCSS variables from tokens.
        
        Args:
            tokens: Token dict from extract()
            mode: Specific mode to generate (e.g., 'light', 'dark'). 
                  If None, generates default mode.
        """
        lines = [
            "// ==================== AUTO-GEN-START ====================",
            "// Design tokens from Figma Variables API",
            "// Generated by FigmaForge",
            "",
        ]
        
        for collection_name, collection_data in tokens.items():
            modes = collection_data.get("modes", {})
            default_mode = collection_data.get("default_mode", "").lower().replace(" ", "-")
            target_mode = mode or default_mode
            
            if not modes:
                continue
            
            # Find the target mode's tokens
            mode_tokens = modes.get(target_mode) or next(iter(modes.values()), {})
            
            if mode_tokens:
                lines.append(f"// {collection_name.title()} tokens ({target_mode})")
                
                for var_name, var_data in mode_tokens.items():
                    value = var_data.get("value", "")
                    var_type = var_data.get("type", "")
                    desc = var_data.get("description", "")
                    
                    if desc:
                        lines.append(f"// {desc}")
                    
                    if var_type == "color":
                        lines.append(f"${var_name}: {value};")
                    elif var_type == "float":
                        lines.append(f"${var_name}: {value}px;")
                    else:
                        lines.append(f"${var_name}: {value};")
                
                lines.append("")
        
        lines.append("// ==================== AUTO-GEN-END ====================")
        
        return "\n".join(lines)
    
    def generate_css_custom_props(self, tokens: Dict[str, Any], mode: str = None) -> str:
        """Generate CSS custom properties from tokens."""
        lines = [
            "/* Design tokens from Figma Variables */",
            ":root {",
        ]
        
        for collection_name, collection_data in tokens.items():
            modes = collection_data.get("modes", {})
            default_mode = collection_data.get("default_mode", "").lower().replace(" ", "-")
            target_mode = mode or default_mode
            mode_tokens = modes.get(target_mode) or next(iter(modes.values()), {})
            
            for var_name, var_data in mode_tokens.items():
                value = var_data.get("value", "")
                var_type = var_data.get("type", "")
                
                if var_type == "float":
                    lines.append(f"  --{var_name}: {value}px;")
                else:
                    lines.append(f"  --{var_name}: {value};")
        
        lines.append("}")
        
        return "\n".join(lines)
