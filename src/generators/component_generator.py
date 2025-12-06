"""Orchestrates Angular component generation from Figma designs."""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

from ..figma.types import FigmaNode, FigmaComponent
from ..figma.client import FigmaClient
from ..figma.normalizer import FigmaNormalizer
from ..extractors.assets import AssetExtractor
from ..utils.console import console
from .html_generator import HTMLGenerator
from .typescript_generator import TypeScriptGenerator
from .scss_generator import SCSSComponentGenerator


class ComponentGenerator:
    """Generates Angular components from Figma designs."""
    
    AUTO_GEN_START = "==================== AUTO-GEN-START ===================="
    AUTO_GEN_END = "==================== AUTO-GEN-END ===================="
    
    def __init__(
        self,
        figma_client: FigmaClient,
        output_path: str,
        assets_output_path: str,
        style_format: str = "scss"
    ):
        self.client = figma_client
        self.output_path = output_path
        self.assets_output_path = assets_output_path
        self.style_format = style_format
        self.normalizer = FigmaNormalizer()
        self.asset_extractor = AssetExtractor(figma_client)
    
    def generate_component(
        self,
        file_key: str,
        node_id: str,
        component_name: str,
        regenerate: bool = False
    ) -> Dict[str, Any]:
        """Generate Angular component files from a Figma node."""
        console.print(f"\n[bold cyan]🚀 Generating component: {component_name}[/bold cyan]")
        
        nodes_data = self.client.get_file_nodes(file_key, [node_id])
        
        if not nodes_data or node_id not in nodes_data:
            raise ValueError(f"Node {node_id} not found in Figma file")
        
        node_wrapper = nodes_data[node_id]
        node: FigmaNode = node_wrapper.get("document") or node_wrapper
        
        component: FigmaComponent = self.normalizer.normalize_node(node)
        
        console.print("[cyan]📦 Extracting assets...[/cyan]")
        asset_paths = self.asset_extractor.extract_assets(
            file_key=file_key,
            asset_node_ids=component["assets"],
            output_dir=self.assets_output_path,
            component_name=component_name
        )
        
        component_dir = Path(self.output_path) / component_name
        component_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        # Generate HTML
        console.print("[cyan]📝 Generating HTML template...[/cyan]")
        html_gen = HTMLGenerator(component_name)
        html_content = html_gen.generate_template(node, asset_paths)
        html_file = component_dir / f"{component_name}.component.html"
        
        if regenerate and html_file.exists():
            html_content = self._merge_generated_content(str(html_file), html_content, "html")
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        generated_files.append(str(html_file))
        console.print(f"  [green]✓ {html_file.name}[/green]")
        
        # Generate TypeScript
        console.print("[cyan]📝 Generating TypeScript component...[/cyan]")
        ts_gen = TypeScriptGenerator(component_name)
        ts_content = ts_gen.generate_component(node)
        ts_file = component_dir / f"{component_name}.component.ts"
        
        if regenerate and ts_file.exists():
            ts_content = self._merge_generated_content(str(ts_file), ts_content, "typescript")
        
        with open(ts_file, 'w', encoding='utf-8') as f:
            f.write(ts_content)
        generated_files.append(str(ts_file))
        console.print(f"  [green]✓ {ts_file.name}[/green]")
        
        # Generate SCSS
        console.print("[cyan]📝 Generating SCSS styles...[/cyan]")
        scss_gen = SCSSComponentGenerator(component_name)
        scss_content = scss_gen.generate_scss(node, import_tokens=True)
        scss_file = component_dir / f"{component_name}.component.scss"
        
        if regenerate and scss_file.exists():
            scss_content = self._merge_generated_content(str(scss_file), scss_content, "scss")
        
        with open(scss_file, 'w', encoding='utf-8') as f:
            f.write(scss_content)
        generated_files.append(str(scss_file))
        console.print(f"  [green]✓ {scss_file.name}[/green]")
        
        console.print(f"\n[bold green]✅ Component generated successfully![/bold green]")
        console.print(f"[dim]Location: {component_dir}[/dim]\n")
        
        return {
            "success": True,
            "component_name": component_name,
            "component_path": str(component_dir),
            "files": generated_files,
            "assets": list(asset_paths.values())
        }
    
    def _merge_generated_content(self, existing_file_path: str, new_content: str, file_type: str) -> str:
        """Merge new content with existing file, preserving custom code."""
        try:
            with open(existing_file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        except FileNotFoundError:
            return new_content
        
        existing_custom = self._extract_custom_code(existing_content)
        
        if existing_custom:
            if file_type == "typescript":
                merged = new_content.rsplit("}", 1)
                if len(merged) == 2:
                    return merged[0] + "\n" + existing_custom + "\n}"
            elif file_type in ["html", "scss"]:
                return new_content + "\n" + existing_custom
        
        return new_content
    
    def _extract_custom_code(self, content: str) -> str:
        """Extract code outside AUTO-GEN blocks."""
        pattern = re.compile(r"// " + re.escape(self.AUTO_GEN_END) + r"(.*)", re.DOTALL)
        match = pattern.search(content)
        
        if match:
            return match.group(1).strip()
        
        pattern = re.compile(r"<!-- " + re.escape(self.AUTO_GEN_END) + r" -->(.*)", re.DOTALL)
        match = pattern.search(content)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _extract_generated_code(self, content: str) -> str:
        """Extract only the AUTO-GEN section."""
        pattern = re.compile(
            r"(" + re.escape(self.AUTO_GEN_START) + r".*?" + re.escape(self.AUTO_GEN_END) + r")",
            re.DOTALL
        )
        match = pattern.search(content)
        return match.group(1) if match else content
