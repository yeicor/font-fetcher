from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Font:
    """The full name of the font."""
    name: str

    """The available styles for the font (None if not yet known)."""
    styles: List[str] = None


class FontRepo(ABC):
    """Abstract base class for font repositories, i.e., sources from which fonts can be fetched."""

    @abstractmethod
    def search_font(self, font_name: str) -> List[Font]:
        """Search for a font by its name and return a list of Font objects with similar names, sorted by relevance."""
        pass

    @abstractmethod
    def download_font(self, out_dir: Path, font: Font, style: str = "Regular") -> Path:
        """Download a specific style of the font to the specified output directory and return the path to the font file.

        Note that styles should be fuzzy matched and the closest style to the given string should be returned."""
        pass
