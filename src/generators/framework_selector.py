"""Framework selector for multi-framework component generation.

Provides a unified interface to select and use different framework generators.
"""

from typing import Dict, Any, List, Optional, Literal
from pathlib import Path
from ..figma.types import FigmaNode


FrameworkType = Literal["angular", "react", "vue"]


class FrameworkSelector:
    """Selects and configures the appropriate generator for a framework.
    
    Supported frameworks:
    - angular: Angular standalone components with TypeScript + SCSS
    - react: React functional components with TypeScript + CSS Modules
    - vue: Vue 3 SFCs with TypeScript + <style scoped> (planned)
    """
    
    SUPPORTED_FRAMEWORKS = ["angular", "react"]
    
    @staticmethod
    def get_file_extensions(framework: FrameworkType) -> Dict[str, str]:
        """Get file extensions for each generated file type."""
        extensions = {
            "angular": {
                "component": ".component.ts",
                "template": ".component.html",
                "style": ".component.scss"
            },
            "react": {
                "component": ".tsx",
                "style": ".module.css"
            },
            "vue": {
                "component": ".vue"
            }
        }
        return extensions.get(framework, extensions["angular"])
    
    @staticmethod
    def get_output_files(
        framework: FrameworkType, 
        component_name: str, 
        component_dir: Path
    ) -> Dict[str, Path]:
        """Get output file paths for a framework."""
        if framework == "react":
            # Pascal case for React components
            pascal_name = "".join(word.capitalize() for word in component_name.replace("-", " ").split())
            return {
                "component": component_dir / f"{pascal_name}.tsx",
                "style": component_dir / f"{pascal_name}.module.css"
            }
        elif framework == "vue":
            pascal_name = "".join(word.capitalize() for word in component_name.replace("-", " ").split())
            return {
                "component": component_dir / f"{pascal_name}.vue"
            }
        else:  # angular
            return {
                "component": component_dir / f"{component_name}.component.ts",
                "template": component_dir / f"{component_name}.component.html",
                "style": component_dir / f"{component_name}.component.scss"
            }
    
    @staticmethod
    def is_supported(framework: str) -> bool:
        """Check if a framework is supported."""
        return framework.lower() in FrameworkSelector.SUPPORTED_FRAMEWORKS
    
    @staticmethod
    def list_frameworks() -> List[str]:
        """List all supported frameworks."""
        return FrameworkSelector.SUPPORTED_FRAMEWORKS.copy()
