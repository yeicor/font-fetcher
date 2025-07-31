import logging
import tempfile
from pathlib import Path

import pytest

from font_fetcher import repo_registry
from font_fetcher.repo import FontRepo


@pytest.mark.parametrize(["repo", "font_name", "style"], [(repo, "Open Sans", "Regular") for repo in repo_registry])
def test_all_repos(repo: FontRepo, font_name: str, style: str):
    """Test fetching fonts that should be available on all repositories"""
    logging.basicConfig(level=logging.DEBUG)

    font_name = "Open Sans"
    style = "Regular"

    found_fonts = repo.search_font(font_name)
    assert len(found_fonts) > 0 and found_fonts[0].name.lower() == font_name.lower(), \
        f"Font {font_name} not found in {repo.__class__.__name__}: {found_fonts}"
    out_path = tempfile.TemporaryDirectory()
    font_path = repo.download_font(Path(out_path.name), found_fonts[0], style)
    assert font_path is not None, f"Failed to download font {font_name} with style {style} from {repo.__class__.__name__}"
    assert font_path.is_file(), f"Downloaded font path {font_path} is not a file in {repo.__class__.__name__}"
    assert font_path.suffix.lower() in [".ttf", ".otf"], \
        f"Downloaded font {font_name} with style {style} has unsupported file extension {font_path.suffix} in {repo.__class__.__name__}"
