"""Orchestrates component generation from Figma designs."""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, Literal

from ..figma.types import FigmaNode, FigmaComponent
from ..figma.client import FigmaClient
from ..figma.normalizer import FigmaNormalizer
from ..extractors.assets import AssetExtractor
from ..extractors.variants import VariantExtractor
from ..utils.console import console
from .html_generator import HTMLGenerator
from .typescript_generator import TypeScriptGenerator
from .scss_generator import SCSSComponentGenerator
from .tailwind_generator import TailwindGenerator
from .react_generator import ReactGenerator
from .vue_generator import VueGenerator
from .webcomponent_generator import WebComponentGenerator


class ComponentGenerator:
    """Generates components from Figma designs (Angular, React, Vue, Web Components)."""
    
    AUTO_GEN_START = "==================== AUTO-GEN-START ===================="
    AUTO_GEN_END = "==================== AUTO-GEN-END ===================="
    
    def __init__(
        self,
        figma_client: FigmaClient,
        output_path: str,
        assets_output_path: str,
        style_format: str = "scss",
        responsive_mode: bool = False,
        framework: Literal["angular", "react", "vue", "webcomponent"] = "angular"
    ):
        self.client = figma_client
        self.output_path = output_path
        self.assets_output_path = assets_output_path
        self.style_format = style_format
        self.responsive_mode = responsive_mode
        self.framework = framework
        self.normalizer = FigmaNormalizer()
        self.asset_extractor = AssetExtractor(figma_client)
        self.variant_extractor = VariantExtractor()
    
    def generate_component(
        self,
        file_key: str,
        node_id: str,
        component_name: str,
        regenerate: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Generate Angular component files from a Figma node.
        
        Args:
            file_key: Figma file key
            node_id: Node ID to generate from
            component_name: Name for the Angular component
            regenerate: If True, merge with existing files
            dry_run: If True, return generated code without writing files
        """
        mode = "preview" if dry_run else "generating"
        console.print(f"\n[bold cyan]🚀 {'Previewing' if dry_run else 'Generating'} component: {component_name}[/bold cyan]")
        
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
        
        # Collect inline SVGs for small assets
        inline_svgs = {}
        for node_id, rel_path in asset_paths.items():
            if rel_path.endswith('.svg'):
                # Construct absolute path from relative path
                abs_path = Path(self.assets_output_path).parent / rel_path
                if abs_path.exists() and self.asset_extractor.should_inline_asset(str(abs_path)):
                    svg_content = self.asset_extractor.get_inline_svg(str(abs_path))
                    if svg_content:
                        inline_svgs[node_id] = self.asset_extractor.optimize_svg(svg_content)
                        console.print(f"  [dim]• Inlining small SVG: {abs_path.name}[/dim]")
        
        component_dir = Path(self.output_path) / component_name
        
        # Check for component variants (COMPONENT_SET)
        variant_info = self.variant_extractor.extract_variants(node)
        variant_inputs = []
        
        if variant_info:
            console.print(f"[cyan]🔀 Detected {len(variant_info.get('properties', []))} variant properties[/cyan]")
            variant_inputs = self.variant_extractor.generate_angular_inputs(variant_info)
            for inp in variant_inputs:
                console.print(f"  [dim]• @Input() {inp['name']}: {inp['type']}[/dim]")
        
        # Generate based on framework
        if self.framework == "react":
            return self._generate_react_component(
                node, component_name, component_dir, asset_paths, inline_svgs, 
                variant_inputs, dry_run
            )
        elif self.framework == "vue":
            return self._generate_vue_component(
                node, component_name, component_dir, asset_paths, inline_svgs, 
                variant_inputs, dry_run
            )
        elif self.framework == "webcomponent":
            return self._generate_webcomponent(
                node, component_name, component_dir, asset_paths, inline_svgs, 
                variant_inputs, dry_run
            )
        
        # Angular generation (default)
        console.print("[cyan]📝 Generating HTML template...[/cyan]")
        html_gen = HTMLGenerator(component_name)
        html_content = html_gen.generate_template(node, asset_paths, inline_svgs)
        html_file = component_dir / f"{component_name}.component.html"
        
        console.print("[cyan]📝 Generating TypeScript component...[/cyan]")
        ts_gen = TypeScriptGenerator(component_name, variant_inputs=variant_inputs)
        ts_content = ts_gen.generate_component(node)
        ts_file = component_dir / f"{component_name}.component.ts"
        
        # Generate styles based on style_format
        if self.style_format == "tailwind":
            console.print("[cyan]📝 Generating Tailwind classes...[/cyan]")
            tailwind_gen = TailwindGenerator(component_name, responsive_mode=self.responsive_mode)
            tailwind_classes = tailwind_gen.generate_classes(node)
            
            # Generate a Tailwind-compatible SCSS file with @apply or minimal CSS
            scss_content = self._generate_tailwind_scss(component_name, tailwind_classes)
            scss_file = component_dir / f"{component_name}.component.scss"
            
            # Also save Tailwind class definitions for reference
            tailwind_file = component_dir / f"{component_name}.tailwind.json"
            import json
            tailwind_json = json.dumps(tailwind_classes, indent=2)
        else:
            console.print("[cyan]📝 Generating SCSS styles...[/cyan]")
            scss_gen = SCSSComponentGenerator(component_name, responsive_mode=self.responsive_mode)
            scss_content = scss_gen.generate_scss(node, import_tokens=True)
            scss_file = component_dir / f"{component_name}.component.scss"
            tailwind_json = None
            tailwind_file = None
        
        # Collect generated content
        generated_content = {
            "html": {"file": str(html_file), "content": html_content},
            "ts": {"file": str(ts_file), "content": ts_content},
            "scss": {"file": str(scss_file), "content": scss_content},
        }
        
        if tailwind_json:
            generated_content["tailwind"] = {"file": str(tailwind_file), "content": tailwind_json}
        
        # Return early for dry run
        if dry_run:
            return {
                "success": True,
                "component_name": component_name,
                "component_path": str(component_dir),
                "files": [],
                "assets": list(asset_paths.values()),
                "generated_content": generated_content,
                "dry_run": True
            }
        
        # Write files
        component_dir.mkdir(parents=True, exist_ok=True)
        generated_files = []
        
        if regenerate and html_file.exists():
            html_content = self._merge_generated_content(str(html_file), html_content, "html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        generated_files.append(str(html_file))
        console.print(f"  [green]✓ {html_file.name}[/green]")
        
        if regenerate and ts_file.exists():
            ts_content = self._merge_generated_content(str(ts_file), ts_content, "typescript")
        with open(ts_file, 'w', encoding='utf-8') as f:
            f.write(ts_content)
        generated_files.append(str(ts_file))
        console.print(f"  [green]✓ {ts_file.name}[/green]")
        
        if regenerate and scss_file.exists():
            scss_content = self._merge_generated_content(str(scss_file), scss_content, "scss")
        with open(scss_file, 'w', encoding='utf-8') as f:
            f.write(scss_content)
        generated_files.append(str(scss_file))
        console.print(f"  [green]✓ {scss_file.name}[/green]")
        
        # Write Tailwind JSON if generated
        if tailwind_json and tailwind_file:
            with open(tailwind_file, 'w', encoding='utf-8') as f:
                f.write(tailwind_json)
            generated_files.append(str(tailwind_file))
            console.print(f"  [green]✓ {tailwind_file.name}[/green]")
        
        console.print(f"\n[bold green]✅ Component generated successfully![/bold green]")
        console.print(f"[dim]Location: {component_dir}[/dim]\n")
        
        return {
            "success": True,
            "component_name": component_name,
            "component_path": str(component_dir),
            "files": generated_files,
            "assets": list(asset_paths.values())
        }
    
    def _generate_tailwind_scss(self, component_name: str, tailwind_classes: Dict[str, str]) -> str:
        """Generate a minimal SCSS file with Tailwind @apply directives.
        
        For Tailwind projects, the actual styling is in the HTML via class attrs.
        This SCSS file provides a fallback and documents the class mapping.
        """
        lines = [
            "// ==================== AUTO-GEN-START ====================",
            "// Generated from Figma - Tailwind mode",
            "// Use the Tailwind classes directly in HTML, or @apply in SCSS",
            "",
            f".{component_name} {{",
            "  // Root component - styling via Tailwind classes in template",
            "}",
            "",
            "// Class mapping reference:",
        ]
        
        for element_name, classes in tailwind_classes.items():
            safe_name = element_name.replace(" ", "-").replace("/", "-")
            lines.append(f"// .{safe_name}: {classes}")
        
        lines.extend([
            "",
            "// ==================== AUTO-GEN-END ====================",
            ""
        ])
        
        return "\n".join(lines)
    
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
    
    def _generate_react_component(
        self,
        node,
        component_name: str,
        component_dir: Path,
        asset_paths: Dict[str, str],
        inline_svgs: Dict[str, str],
        variant_inputs: list,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Generate React component files."""
        from ..utils.css import to_pascal_case
        
        pascal_name = to_pascal_case(component_name)
        
        console.print("[cyan]📝 Generating React component...[/cyan]")
        react_gen = ReactGenerator(component_name, variant_inputs=variant_inputs)
        react_result = react_gen.generate_component(node, asset_paths, inline_svgs)
        
        tsx_content = react_result["tsx"]
        css_content = react_result["css"]
        
        tsx_file = component_dir / f"{pascal_name}.tsx"
        css_file = component_dir / f"{pascal_name}.module.css"
        
        generated_content = {
            "tsx": {"file": str(tsx_file), "content": tsx_content},
            "css": {"file": str(css_file), "content": css_content},
        }
        
        if dry_run:
            return {
                "success": True,
                "component_name": component_name,
                "component_path": str(component_dir),
                "files": [],
                "assets": list(asset_paths.values()),
                "generated_content": generated_content,
                "dry_run": True
            }
        
        # Write files
        component_dir.mkdir(parents=True, exist_ok=True)
        generated_files = []
        
        with open(tsx_file, 'w', encoding='utf-8') as f:
            f.write(tsx_content)
        generated_files.append(str(tsx_file))
        console.print(f"  [green]✓ {tsx_file.name}[/green]")
        
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content)
        generated_files.append(str(css_file))
        console.print(f"  [green]✓ {css_file.name}[/green]")
        
        console.print(f"\n[bold green]✅ React component generated successfully![/bold green]")
        console.print(f"[dim]Location: {component_dir}[/dim]\n")
        
        return {
            "success": True,
            "component_name": component_name,
            "component_path": str(component_dir),
            "files": generated_files,
            "assets": list(asset_paths.values())
        }
    
    def _generate_vue_component(
        self,
        node,
        component_name: str,
        component_dir: Path,
        asset_paths: Dict[str, str],
        inline_svgs: Dict[str, str],
        variant_inputs: list,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Generate Vue 3 SFC component."""
        from ..utils.css import to_pascal_case
        
        pascal_name = to_pascal_case(component_name)
        
        console.print("[cyan]📝 Generating Vue 3 SFC...[/cyan]")
        vue_gen = VueGenerator(component_name, variant_inputs=variant_inputs)
        vue_result = vue_gen.generate_component(node, asset_paths, inline_svgs)
        
        vue_content = vue_result["vue"]
        vue_file = component_dir / f"{pascal_name}.vue"
        
        if dry_run:
            return {
                "success": True,
                "component_name": component_name,
                "component_path": str(component_dir),
                "files": [],
                "generated_content": {"vue": {"file": str(vue_file), "content": vue_content}},
                "dry_run": True
            }
        
        component_dir.mkdir(parents=True, exist_ok=True)
        
        with open(vue_file, 'w', encoding='utf-8') as f:
            f.write(vue_content)
        console.print(f"  [green]✓ {vue_file.name}[/green]")
        
        console.print(f"\n[bold green]✅ Vue component generated successfully![/bold green]")
        console.print(f"[dim]Location: {component_dir}[/dim]\n")
        
        return {
            "success": True,
            "component_name": component_name,
            "component_path": str(component_dir),
            "files": [str(vue_file)],
            "assets": list(asset_paths.values())
        }
    
    def _generate_webcomponent(
        self,
        node,
        component_name: str,
        component_dir: Path,
        asset_paths: Dict[str, str],
        inline_svgs: Dict[str, str],
        variant_inputs: list,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Generate Web Component (Custom Element)."""
        from ..utils.css import to_pascal_case
        
        pascal_name = to_pascal_case(component_name)
        
        console.print("[cyan]📝 Generating Web Component...[/cyan]")
        wc_gen = WebComponentGenerator(component_name, variant_inputs=variant_inputs)
        wc_result = wc_gen.generate_component(node, asset_paths, inline_svgs)
        
        js_content = wc_result["js"]
        js_file = component_dir / f"{pascal_name}.js"
        
        if dry_run:
            return {
                "success": True,
                "component_name": component_name,
                "component_path": str(component_dir),
                "files": [],
                "generated_content": {"js": {"file": str(js_file), "content": js_content}},
                "dry_run": True
            }
        
        component_dir.mkdir(parents=True, exist_ok=True)
        
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
        console.print(f"  [green]✓ {js_file.name}[/green]")
        
        console.print(f"\n[bold green]✅ Web Component generated successfully![/bold green]")
        console.print(f"[dim]Location: {component_dir}[/dim]\n")
        
        return {
            "success": True,
            "component_name": component_name,
            "component_path": str(component_dir),
            "files": [str(js_file)],
            "assets": list(asset_paths.values())
        }
