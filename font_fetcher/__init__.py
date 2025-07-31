import os
import sys
from pathlib import Path
from typing import Optional

from font_fetcher.misc import logger
from font_fetcher.repo_registry import repo_registry


def _get_cache_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "fontfetcher"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "fontfetcher"
    else:  # Assuming Linux or other Unix-like systems
        return Path.home() / ".cache" / "fontfetcher"


_CACHE_DIR = _get_cache_dir()
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_font(font_name: str, style: str, exact: bool = True) -> Path:
    """Fetches font from cache or remote if not cached."""
    cached_font = fetch_font_cached(font_name, style)
    if cached_font is not None:
        return cached_font
    return fetch_font_remote(font_name, style, exact)


def _cached_basename(font_name: str, style: str, ext: str) -> str:
    """Generates a cached font basename based on font name, style, and extension."""
    return f"{font_name}-{style}.{ext.lower()}"


def fetch_font_cached(font_name: str, style: str = "Regular") -> Optional[Path]:
    """Fetches font from cache if available."""
    logger.debug(f"Looking for cached font '{font_name}' with style '{style}'")
    for cached_basename in [_cached_basename(font_name, style, "ttf"), _cached_basename(font_name, style, "otf")]:
        if cached_basename in os.listdir(_CACHE_DIR):
            cached_path = _CACHE_DIR / cached_basename
            if cached_path.exists():
                logger.debug(f"Found cached font: {cached_path}")
                return cached_path
    return None


def fetch_font_remote(font_name: str, style: str = "Regular", exact: bool = True) -> Path:
    """"""
    logger.debug(f"Fetching font '{font_name}' with style '{style}'")
    for repo in repo_registry:
        fonts = repo.search_font(font_name)
        if len(fonts) == 0 or (exact and fonts[0].name.lower() != font_name.lower()):
            logger.debug(f"Font '{font_name}' not found (exactly) in repository: {repo.__class__.__name__}")
            continue

        downloaded = repo.download_font(_CACHE_DIR, fonts[0], style)
        # Cache with user-provided name and style in case they are not exact matches
        cached_path = _CACHE_DIR / _cached_basename(font_name, style, downloaded.suffix.lower()[1:])
        if downloaded != cached_path:
            logger.debug(f"Moving downloaded font from {downloaded} to {cached_path}")
            if cached_path.exists():
                logger.warning(f"Cached font already exists, removing: {cached_path}")
                cached_path.unlink()
            downloaded.rename(cached_path)

        logger.debug(f"Font cached to: {cached_path}")
        return cached_path

    raise FileNotFoundError(f"Font '{font_name}' with style '{style}' not found in any registered repositories.")
