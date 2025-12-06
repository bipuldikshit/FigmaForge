"""Download and optimize assets from Figma."""

import os
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional
from ..figma.client import FigmaClient
from ..utils.console import console


class AssetExtractor:
    """Downloads images and vectors from Figma files."""
    
    INLINE_THRESHOLD = 2048  # 2KB - assets smaller than this can be inlined
    
    def __init__(self, figma_client: FigmaClient):
        self.client = figma_client
    
    def extract_assets(
        self,
        file_key: str,
        asset_node_ids: List[str],
        output_dir: str,
        component_name: str
    ) -> Dict[str, str]:
        """Download assets and return mapping of node IDs to file paths."""
        if not asset_node_ids:
            return {}
        
        console.print(f"[cyan]🖼  Extracting {len(asset_node_ids)} asset(s)...[/cyan]")
        
        asset_dir = Path(output_dir) / component_name
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        asset_paths = {}
        
        # Try SVG first, fall back to PNG
        try:
            svg_urls = self.client.get_image_urls(file_key, asset_node_ids, format="svg")
            
            for node_id, url in svg_urls.items():
                if url:
                    asset_name = f"asset-{node_id.replace(':', '-')}.svg"
                    asset_path = asset_dir / asset_name
                    self._download_asset(url, str(asset_path))
                    asset_paths[node_id] = f"assets/figma/{component_name}/{asset_name}"
                    
        except Exception as e:
            console.print(f"[yellow]⚠ SVG failed, trying PNG: {e}[/yellow]")
            
            try:
                png_urls = self.client.get_image_urls(file_key, asset_node_ids, format="png", scale=2.0)
                
                for node_id, url in png_urls.items():
                    if url:
                        asset_name = f"asset-{node_id.replace(':', '-')}.png"
                        asset_path = asset_dir / asset_name
                        self._download_asset(url, str(asset_path))
                        asset_paths[node_id] = f"assets/figma/{component_name}/{asset_name}"
                        
            except Exception as e:
                console.print(f"[red]✗ Asset extraction failed: {e}[/red]")
        
        console.print(f"[green]✓ Extracted {len(asset_paths)} asset(s)[/green]")
        return asset_paths
    
    def should_inline_asset(self, asset_path: str) -> bool:
        """Check if asset is small enough to inline."""
        if not os.path.exists(asset_path):
            return False
        return os.path.getsize(asset_path) < self.INLINE_THRESHOLD
    
    def get_inline_svg(self, asset_path: str) -> Optional[str]:
        """Read SVG content for inlining."""
        if not asset_path.endswith('.svg'):
            return None
        
        try:
            with open(asset_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            console.print(f"[yellow]⚠ Failed to read SVG: {e}[/yellow]")
            return None
    
    def optimize_svg(self, svg_content: str) -> str:
        """Remove comments and extra whitespace from SVG."""
        if svg_content.startswith('<?xml'):
            svg_content = svg_content.split('?>', 1)[1].strip()
        
        svg_content = re.sub(r'<!--.*?-->', '', svg_content, flags=re.DOTALL)
        svg_content = re.sub(r'>\s+<', '><', svg_content)
        return svg_content.strip()
    
    def _download_asset(self, url: str, output_path: str) -> None:
        """Download asset from URL and save to disk."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            size_kb = len(response.content) / 1024
            console.print(f"  [dim]• {Path(output_path).name} ({size_kb:.1f} KB)[/dim]")
            
        except Exception as e:
            raise Exception(f"Download failed: {e}")
