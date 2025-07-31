from typing import Optional

import pytest
from OCP.OCP.Font import Font_SystemFont

from font_fetcher.ocp import install_ocp_font_hook, uninstall_ocp_font_hook

try:  # Skip tests if OCP is not installed (optional dependency)
    from OCP.Font import Font_FontMgr

    have_ocp = True
except ImportError:
    have_ocp = False
try:  # Skip tests if build123d is not installed (optional dependency)
    # noinspection PyUnresolvedReferences
    from build123d import Text, FontStyle

    have_build123d = True
except ImportError:
    have_build123d = False


@pytest.mark.skipif(not have_ocp, reason="OCP is not installed")
def test_install_ocp_font_hook():
    """Test the installation of the OCP font hook."""

    first_font = do_test_font("Poppins")
    assert first_font is None, "Poppins should not be found before installing the hook"

    install_ocp_font_hook()

    assert do_test_font("Poppins") is not None, "Poppins should be found after installing the hook"
    assert do_test_font("Poppins") is not None, "Poppins should be found after installing the hook (cached)"

    uninstall_ocp_font_hook()

    last_font = do_test_font("Poppins")
    assert last_font is None, "Poppins should not be found after uninstalling the hook"


@pytest.mark.skipif(not have_build123d, reason="build123d is not installed")
@pytest.mark.parametrize("font_name", ["Poppins", "Open Sans", "Arial"]) # Arial should be renamed to DejaVu Sans
def test_build123d(font_name):
    """Test that build123d can create text with a specific font."""
    from build123d import Text

    # Without the hook, this would fall back to a any system font
    wires_len = lambda s: sum(wire.length for wire in s.wires())
    text1 = Text("Hello, World!", 10, font=font_name, font_style=FontStyle.BOLD)
    text2 = Text("Hello, World!", 10, font=font_name, font_style=FontStyle.BOLD)
    assert wires_len(text1) == wires_len(text2), "Text objects should be equal when created with the same parameters"
    # export_stl(extrude(text1, 1), "test_poppins_before_hook.stl")

    install_ocp_font_hook()

    # Create text with a specific font
    text = Text("Hello, World!", 10, font=font_name, font_style=FontStyle.BOLD)
    if font_name != "Arial": # This font (or DejaVu Sans) is commonly present in the system
        assert wires_len(text) != wires_len(text1), "Text objects should use different fonts after hook installation"
    # export_stl(extrude(text, 1), "test_poppins.stl")

    uninstall_ocp_font_hook()


def do_test_font(font_name: str) -> Optional[Font_SystemFont]:
    """Helper function to test if a font can be found."""
    from OCP.TCollection import TCollection_AsciiString
    from OCP.Font import Font_FontAspect, Font_StrictLevel, Font_FontMgr

    # noinspection PyArgumentList
    font_mgr = Font_FontMgr.GetInstance_s()
    font = font_mgr.FindFont(TCollection_AsciiString(font_name), Font_StrictLevel.Font_StrictLevel_Strict,
                             Font_FontAspect.Font_FontAspect_Bold, False)
    return font  # No exception means the font was found successfully
