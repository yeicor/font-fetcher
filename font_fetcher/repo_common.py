import os
import shutil
import tempfile
from difflib import get_close_matches
from pathlib import Path

import requests

from font_fetcher.misc import logger
from font_fetcher.repo import Font


def sort_fonts_by_name(wanted_name: str, font_list: list[Font]) -> list[Font]:
    """Sorts a list of Font objects by their name, prioritizing those that match the wanted name (some repos
    sort by popularity making matching names appear further down the list)."""
    font_to_name = {font.name.lower(): font for font in font_list}
    wanted_name = wanted_name.lower()
    # Sort by exact match first, then by close matches
    sorted_names = get_close_matches(wanted_name, font_to_name.keys(), n=len(font_to_name), cutoff=0.0)
    logger.debug(f"Sorted retrieved fonts by name: {sorted_names}")
    sorted_fonts = [font_to_name[name] for name in sorted_names if name in font_to_name]
    return sorted_fonts


def download_font_url(out_dir: Path, font: Font, style: str, url: str) -> Path:
    """If a repo provides a direct download URL for a compressed font file containing all of its styles,
    this function can be used to download and extract the font file from the URL."""
    # Download compressed file to a temporary location
    tmp_dir = tempfile.TemporaryDirectory()
    response = requests.get(url)
    if response.status_code != 200:
        raise ConnectionError(f"Failed to download font '{font.name}': {response.status_code}")
    mime = response.headers["Content-Type"]
    logger.debug(f"Downloading font '{font.name}' with MIME type '{mime}' from {url}")
    dl_font_path = Path(tmp_dir.name) / (font.name + "." + {
        "application/zip": "zip",
        "application/x-zip-compressed": "zip",
        "application/x-tar": "tar",
        "application/gzip": "gz",
        "application/x-gzip": "gz",
        "application/x-bzip2": "bz2",
        "application/x-xz": "xz",
        "application/x-7z-compressed": "7z",
    }.get(mime, "zip"))

    # Extract the compressed file
    logger.debug(f"Extracting '{dl_font_path}' and looking for style '{style}'")
    with open(dl_font_path, 'wb') as f:
        f.write(response.content)
    shutil.unpack_archive(dl_font_path, tmp_dir.name)
    os.remove(dl_font_path)

    # Fuzzy-find the matching font style
    font_files = list(
        [f for f in Path(tmp_dir.name).glob("**/*") if f.is_file() and f.suffix.lower() in {".ttf", ".otf"}])
    if not font_files:
        raise FileNotFoundError(f"No font files found in the downloaded archive for '{font.name}'.")
    matching_files = get_close_matches(style.lower(), [f.name.lower() for f in font_files], n=1, cutoff=0.0)
    matching_file = next(f for f in font_files if f.name.lower() == matching_files[0])
    logger.debug(
        f"Chose '{matching_file.relative_to(tmp_dir.name).name}' for style '{style}' out of: "
        f"{[f.relative_to(tmp_dir.name).name for f in font_files]}")

    # Move the font file to the output path and  cleanup
    out_path = out_dir / matching_file.name
    shutil.move(matching_file, out_path)
    tmp_dir.cleanup()  # Clean up the temporary directory
    return out_path
