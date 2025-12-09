"""Figma API client with rate limiting, retry logic, and caching."""

import os
import requests
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from .types import FigmaFile, FigmaNode
from ..utils.console import console
from ..cache import get_cache
from ..exceptions import (
    FigmaAPIError,
    FigmaAuthError,
    FigmaRateLimitError,
    FigmaNotFoundError,
    FigmaConnectionError,
    MissingTokenError
)

load_dotenv()


class FigmaClient:
    """Client for the Figma REST API with caching support."""
    
    BASE_URL = "https://api.figma.com/v1"
    MAX_RETRIES = 3
    RETRY_DELAY = 60
    
    def __init__(self, token: Optional[str] = None, use_cache: bool = True):
        """Initialize with token from parameter or FIGMA_TOKEN env var.
        
        Args:
            token: Figma API token (optional, uses FIGMA_TOKEN env var)
            use_cache: Whether to use local cache (default: True)
        """
        self.token = token or os.getenv("FIGMA_TOKEN")
        if not self.token:
            raise MissingTokenError()
        
        self.session = requests.Session()
        self.session.headers.update({"X-Figma-Token": self.token})
        self.cache = get_cache(enabled=use_cache)
    
    def _make_request(
        self, 
        endpoint: str, 
        method: str = "GET", 
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic for rate limits."""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.request(method, url, params=params, timeout=30)
            
            if response.status_code == 429:
                if retry_count < self.MAX_RETRIES:
                    console.print(
                        f"[yellow]⚠ Rate limit hit. Retrying in {self.RETRY_DELAY}s "
                        f"({retry_count + 1}/{self.MAX_RETRIES})[/yellow]"
                    )
                    time.sleep(self.RETRY_DELAY)
                    return self._make_request(endpoint, method, params, retry_count + 1)
                raise FigmaRateLimitError("Rate limit exceeded. Try again later.")
            
            if response.status_code == 403:
                raise FigmaAuthError(
                    "Invalid Figma token. Check FIGMA_TOKEN in .env file. "
                    "Get a token at: https://www.figma.com/settings"
                )
            
            if response.status_code == 404:
                raise FigmaNotFoundError("Resource not found. Check file key or node ID.")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise FigmaConnectionError("Request timed out.")
        except requests.exceptions.ConnectionError:
            raise FigmaConnectionError("Connection failed. Check internet connection.")
        except requests.exceptions.RequestException as e:
            raise FigmaAPIError(f"Request failed: {e}")
    
    def get_file(self, file_key: str, node_ids: Optional[List[str]] = None, geometry: str = "paths") -> FigmaFile:
        """Fetch a Figma file, optionally filtered to specific nodes."""
        cache_key_parts = [file_key, ",".join(node_ids) if node_ids else "full"]
        
        # Check cache first
        cached = self.cache.get("files", *cache_key_parts)
        if cached:
            console.print(f"[green]⚡ Cache hit for file: {file_key}[/green]")
            return cached.data
        
        params = {}
        if node_ids:
            params["ids"] = ",".join(node_ids)
        if geometry:
            params["geometry"] = geometry
        
        console.print(f"[cyan]📥 Fetching Figma file: {file_key}[/cyan]")
        data = self._make_request(f"files/{file_key}", params=params)
        
        if "document" not in data:
            raise FigmaAPIError("Invalid response: missing document")
        
        # Cache the response
        self.cache.set("files", *cache_key_parts, data=data)
        
        console.print(f"[green]✓ Fetched: {data.get('name', 'Untitled')}[/green]")
        return data
    
    def get_file_nodes(self, file_key: str, node_ids: List[str]) -> Dict[str, FigmaNode]:
        """Fetch specific nodes from a file."""
        cache_key_parts = [file_key, "nodes", ",".join(sorted(node_ids))]
        
        # Check cache first
        cached = self.cache.get("nodes", *cache_key_parts)
        if cached:
            console.print(f"[green]⚡ Cache hit for {len(node_ids)} node(s)[/green]")
            return cached.data
        
        params = {"ids": ",".join(node_ids)}
        console.print(f"[cyan]📥 Fetching {len(node_ids)} node(s) from file: {file_key}[/cyan]")
        
        data = self._make_request(f"files/{file_key}/nodes", params=params)
        
        if "nodes" not in data:
            raise FigmaAPIError("Invalid response: missing nodes")
        
        # Cache the response
        self.cache.set("nodes", *cache_key_parts, data=data["nodes"])
        
        console.print(f"[green]✓ Fetched {len(data['nodes'])} node(s)[/green]")
        return data["nodes"]
    
    def get_image_urls(
        self, 
        file_key: str, 
        node_ids: List[str], 
        format: str = "svg",
        scale: float = 1.0
    ) -> Dict[str, str]:
        """Get export URLs for nodes as images."""
        # Image URLs are short-lived, so we don't cache them
        params = {"ids": ",".join(node_ids), "format": format, "scale": scale}
        
        console.print(f"[cyan]📤 Requesting {format.upper()} exports for {len(node_ids)} node(s)[/cyan]")
        data = self._make_request(f"images/{file_key}", params=params)
        
        if "images" not in data:
            raise FigmaAPIError("Invalid response: missing images")
        
        images = {k: v for k, v in data["images"].items() if v}
        console.print(f"[green]✓ Got {len(images)} export URL(s)[/green]")
        return images
    
    def get_file_styles(self, file_key: str) -> Dict[str, Any]:
        """Get style definitions from a file."""
        console.print(f"[cyan]🎨 Fetching styles from: {file_key}[/cyan]")
        data = self._make_request(f"files/{file_key}/styles")
        console.print("[green]✓ Fetched styles[/green]")
        return data.get("meta", {}).get("styles", {})
    
    def get_local_variables(self, file_key: str) -> Dict[str, Any]:
        """Get local variables from a Figma file.
        
        Uses the Figma Variables API to fetch variable definitions.
        Note: Requires Enterprise plan for full access.
        
        Returns:
            Dict containing 'variables' and 'variableCollections' keys
        """
        console.print(f"[cyan]🔤 Fetching variables from: {file_key}[/cyan]")
        
        try:
            data = self._make_request(f"files/{file_key}/variables/local")
            
            variables = data.get("meta", {}).get("variables", {})
            collections = data.get("meta", {}).get("variableCollections", {})
            
            console.print(f"[green]✓ Fetched {len(variables)} variable(s) in {len(collections)} collection(s)[/green]")
            
            return {
                "variables": variables,
                "variableCollections": collections
            }
        except FigmaAPIError as e:
            # Variables API may not be available on all plans
            console.print(f"[yellow]⚠ Variables API not available: {e}[/yellow]")
            return {"variables": {}, "variableCollections": {}}
    
    def clear_cache(self) -> int:
        """Clear all cached API responses."""
        count = self.cache.clear()
        console.print(f"[yellow]🗑 Cleared {count} cached entries[/yellow]")
        return count

