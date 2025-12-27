import sys
from pathlib import Path
from typing import List
from urllib.parse import urljoin, urlencode

import requests
from bs4 import BeautifulSoup

from font_fetcher.misc import logger
from font_fetcher.repo import FontRepo, Font
from font_fetcher.repo_common import download_font_url, sort_fonts_by_name


class Fonts1001Repo(FontRepo):
    """Repository for fetching fonts from 1001fonts.com."""

    search_url = "https://www.1001fonts.com/search.html"
    search_url_prefix = "https://little-hill-4bc4.yeicor-cloudflare.workers.dev/?url=" if sys.platform == "emscripten" else ""  # Avoid CORS issues

    def search_font(self, font_name: str) -> List[Font]:
        """Search for a font by its name and return a list of Font objects."""
        url = self.search_url_prefix + self.search_url + "?" + urlencode(
            {'search': font_name})  # One page is enough
        response = requests.get(str(url))
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        font_elements = soup.select('.font-list-item')
        fonts = []
        for element in font_elements:
            name = next(element.select_one('.font-title').stripped_strings)  # Also contains other unwanted children
            if name == "":
                logger.info(f"Skipping empty font name in search results for '{font_name}'")
                continue
            font = Font(name=name)
            font._url = urljoin(self.search_url, element.select_one('a.btn-download').get('href'))
            if not font._url:
                logger.info(f"Skipping {font_name} -> {name} as no URL found")
                continue
            fonts.append(font)

        return sort_fonts_by_name(font_name, fonts)

    def download_font(self, out_dir: Path, font: Font, style: str = "Regular") -> Path:
        """Download a specific style of the font to the specified output directory."""
        # noinspection PyUnresolvedReferences,PyProtectedMember
        return download_font_url(out_dir, font, style, self.search_url_prefix + font._url)
