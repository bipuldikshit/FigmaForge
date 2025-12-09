"""Download and optimize assets from Figma using async parallel downloads."""

import os
import re
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from ..figma.client import FigmaClient
from ..utils.console import console


class AssetExtractor:
    """Downloads images and vectors from Figma files with async parallel support."""
    
    INLINE_THRESHOLD = 2048  # 2KB - assets smaller than this can be inlined
    MAX_CONCURRENT = 5  # Max concurrent downloads
    RETRY_ATTEMPTS = 3  # Number of retry attempts
    TIMEOUT_SECONDS = 30
    
    def __init__(self, figma_client: FigmaClient):
        self.client = figma_client
    
    def extract_assets(
        self,
        file_key: str,
        asset_node_ids: List[str],
        output_dir: str,
        component_name: str
    ) -> Dict[str, str]:
        """Download assets and return mapping of node IDs to file paths.
        
        Uses asyncio for parallel downloads when multiple assets are needed.
        """
        if not asset_node_ids:
            return {}
        
        console.print(f"[cyan]🖼  Extracting {len(asset_node_ids)} asset(s)...[/cyan]")
        
        asset_dir = Path(output_dir) / component_name
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        # Run async download
        return asyncio.run(self._extract_assets_async(
            file_key, asset_node_ids, str(asset_dir), component_name
        ))
    
    async def _extract_assets_async(
        self,
        file_key: str,
        asset_node_ids: List[str],
        asset_dir: str,
        component_name: str
    ) -> Dict[str, str]:
        """Async asset extraction with parallel downloads."""
        asset_paths = {}
        
        # Try SVG first, fall back to PNG
        try:
            svg_urls = self.client.get_image_urls(file_key, asset_node_ids, format="svg")
            
            if svg_urls:
                download_tasks = []
                for node_id, url in svg_urls.items():
                    if url:
                        asset_name = f"asset-{node_id.replace(':', '-')}.svg"
                        asset_path = Path(asset_dir) / asset_name
                        relative_path = f"assets/figma/{component_name}/{asset_name}"
                        download_tasks.append(
                            self._download_with_retry(url, str(asset_path), node_id, relative_path)
                        )
                
                # Run downloads in parallel with semaphore
                results = await self._parallel_download(download_tasks)
                
                for node_id, relative_path in results:
                    if node_id and relative_path:
                        asset_paths[node_id] = relative_path
                        
        except Exception as e:
            console.print(f"[yellow]⚠ SVG failed, trying PNG: {e}[/yellow]")
            
            try:
                png_urls = self.client.get_image_urls(file_key, asset_node_ids, format="png", scale=2.0)
                
                if png_urls:
                    download_tasks = []
                    for node_id, url in png_urls.items():
                        if url:
                            asset_name = f"asset-{node_id.replace(':', '-')}.png"
                            asset_path = Path(asset_dir) / asset_name
                            relative_path = f"assets/figma/{component_name}/{asset_name}"
                            download_tasks.append(
                                self._download_with_retry(url, str(asset_path), node_id, relative_path)
                            )
                    
                    results = await self._parallel_download(download_tasks)
                    
                    for node_id, relative_path in results:
                        if node_id and relative_path:
                            asset_paths[node_id] = relative_path
                            
            except Exception as e:
                console.print(f"[red]✗ Asset extraction failed: {e}[/red]")
        
        console.print(f"[green]✓ Extracted {len(asset_paths)} asset(s)[/green]")
        return asset_paths
    
    async def _parallel_download(
        self,
        download_tasks: List
    ) -> List[Tuple[Optional[str], Optional[str]]]:
        """Run download tasks in parallel with concurrency limit."""
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        
        async def bounded_download(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(
            *[bounded_download(task) for task in download_tasks],
            return_exceptions=True
        )
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                console.print(f"[yellow]⚠ Download error: {result}[/yellow]")
                valid_results.append((None, None))
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def _download_with_retry(
        self,
        url: str,
        output_path: str,
        node_id: str,
        relative_path: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Download asset with retry logic."""
        for attempt in range(self.RETRY_ATTEMPTS):
            try:
                await self._download_asset_async(url, output_path)
                return (node_id, relative_path)
            except Exception as e:
                if attempt < self.RETRY_ATTEMPTS - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    console.print(f"[yellow]⚠ Retry {attempt + 1}/{self.RETRY_ATTEMPTS} for {node_id}[/yellow]")
                    await asyncio.sleep(wait_time)
                else:
                    console.print(f"[red]✗ Failed to download {node_id}: {e}[/red]")
                    return (None, None)
        return (None, None)
    
    async def _download_asset_async(self, url: str, output_path: str) -> None:
        """Download asset from URL asynchronously."""
        timeout = aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                
                # Write file synchronously (I/O is blocking but fast for small files)
                with open(output_path, 'wb') as f:
                    f.write(content)
                
                size_kb = len(content) / 1024
                console.print(f"  [dim]• {Path(output_path).name} ({size_kb:.1f} KB)[/dim]")
    
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
        """Remove comments, XML declarations, and extra whitespace from SVG."""
        # Remove XML declaration
        if svg_content.startswith('<?xml'):
            svg_content = svg_content.split('?>', 1)[1].strip()
        
        # Remove comments
        svg_content = re.sub(r'<!--.*?-->', '', svg_content, flags=re.DOTALL)
        
        # Remove excessive whitespace between tags
        svg_content = re.sub(r'>\s+<', '><', svg_content)
        
        # Clean up whitespace in attributes
        svg_content = re.sub(r'\s+', ' ', svg_content)
        
        return svg_content.strip()
