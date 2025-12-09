"""API Response Cache for FigmaForge.

Caches Figma API responses locally to reduce API calls and speed up regeneration.
Uses ETags for conditional requests and auto-expires after configurable TTL.
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Represents a cached API response."""
    data: Dict[str, Any]
    etag: Optional[str]
    timestamp: float
    

class APICache:
    """Local cache for Figma API responses.
    
    Cache Structure:
        ~/.figmaforge/cache/
        ├── files/
        │   └── {file_key_hash}.json
        ├── nodes/
        │   └── {file_key}_{node_ids_hash}.json
        └── images/
            └── {file_key}_{node_ids_hash}_{format}.json
    """
    
    DEFAULT_TTL = 3600 * 24  # 24 hours in seconds
    CACHE_DIR = Path.home() / ".figmaforge" / "cache"
    
    def __init__(self, ttl: int = DEFAULT_TTL, enabled: bool = True):
        """Initialize cache.
        
        Args:
            ttl: Time-to-live in seconds (default: 24 hours)
            enabled: Whether caching is enabled
        """
        self.ttl = ttl
        self.enabled = enabled
        self._ensure_cache_dirs()
    
    def _ensure_cache_dirs(self) -> None:
        """Create cache directories if they don't exist."""
        if not self.enabled:
            return
        for subdir in ["files", "nodes", "images"]:
            (self.CACHE_DIR / subdir).mkdir(parents=True, exist_ok=True)
    
    def _hash_key(self, *args: str) -> str:
        """Generate a hash key from arguments."""
        combined = "_".join(str(a) for a in args)
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    def _get_cache_path(self, category: str, *key_parts: str) -> Path:
        """Get the file path for a cache entry."""
        key = self._hash_key(*key_parts)
        return self.CACHE_DIR / category / f"{key}.json"
    
    def get(self, category: str, *key_parts: str) -> Optional[CacheEntry]:
        """Retrieve a cached entry if valid.
        
        Args:
            category: Cache category (files, nodes, images)
            key_parts: Parts to form the cache key
            
        Returns:
            CacheEntry if found and not expired, None otherwise
        """
        if not self.enabled:
            return None
        
        cache_path = self._get_cache_path(category, *key_parts)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)
            
            # Check expiration
            if time.time() - cached.get("timestamp", 0) > self.ttl:
                cache_path.unlink()  # Delete expired cache
                return None
            
            return CacheEntry(
                data=cached.get("data", {}),
                etag=cached.get("etag"),
                timestamp=cached.get("timestamp", 0)
            )
        except (json.JSONDecodeError, IOError):
            return None
    
    def set(
        self,
        category: str,
        *key_parts: str,
        data: Dict[str, Any],
        etag: Optional[str] = None
    ) -> None:
        """Store data in cache.
        
        Args:
            category: Cache category
            key_parts: Parts to form the cache key
            data: Data to cache
            etag: Optional ETag for conditional requests
        """
        if not self.enabled:
            return
        
        cache_path = self._get_cache_path(category, *key_parts)
        
        cache_entry = {
            "data": data,
            "etag": etag,
            "timestamp": time.time()
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False)
        except IOError:
            pass  # Silently fail on cache write errors
    
    def get_etag(self, category: str, *key_parts: str) -> Optional[str]:
        """Get stored ETag for conditional request."""
        entry = self.get(category, *key_parts)
        return entry.etag if entry else None
    
    def invalidate(self, category: str, *key_parts: str) -> None:
        """Remove a specific cache entry."""
        cache_path = self._get_cache_path(category, *key_parts)
        if cache_path.exists():
            cache_path.unlink()
    
    def clear(self, category: Optional[str] = None) -> int:
        """Clear cache entries.
        
        Args:
            category: If specified, only clear that category. Otherwise clear all.
            
        Returns:
            Number of entries cleared
        """
        count = 0
        
        if category:
            target_dir = self.CACHE_DIR / category
            if target_dir.exists():
                for f in target_dir.glob("*.json"):
                    f.unlink()
                    count += 1
        else:
            for subdir in ["files", "nodes", "images"]:
                target_dir = self.CACHE_DIR / subdir
                if target_dir.exists():
                    for f in target_dir.glob("*.json"):
                        f.unlink()
                        count += 1
        
        return count
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {"total_entries": 0, "total_size_bytes": 0, "categories": {}}
        
        for subdir in ["files", "nodes", "images"]:
            target_dir = self.CACHE_DIR / subdir
            if target_dir.exists():
                files = list(target_dir.glob("*.json"))
                size = sum(f.stat().st_size for f in files)
                stats["categories"][subdir] = {
                    "entries": len(files),
                    "size_bytes": size
                }
                stats["total_entries"] += len(files)
                stats["total_size_bytes"] += size
        
        return stats


# Global cache instance
_cache: Optional[APICache] = None


def get_cache(enabled: bool = True) -> APICache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = APICache(enabled=enabled)
    return _cache
