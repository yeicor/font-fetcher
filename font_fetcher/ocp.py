from pathlib import Path
from threading import Lock
from typing import Dict, Optional

from font_fetcher import fetch_font_cached
from font_fetcher.misc import logger

_original_font_mgr = None
_wrapper_instance = None
_font_hook_lock = Lock()

# From OCP.Font_FontAspect
aspect_to_style: Dict[int, str] = {
    1: "Bold",
    2: "Italic",
    3: "Bold Italic",
}


def install_ocp_font_hook(
    fail_on_not_found: bool = False,
    renames: Optional[Dict[str, str]] = None,
    exact_match: bool = True,
):
    """
    Install the OCP.Font_FontMgr patch to auto-download missing fonts.
    """
    global _original_font_mgr
    global _wrapper_instance

    if renames is None:
        renames = {"Arial": "DejaVu Sans", "build123d": "DejaVu Sans"}

    with _font_hook_lock:
        if _original_font_mgr is not None:
            logger.info("OCP Font_FontMgr patch already installed. Skipping installation.")
            return

        try:
            from OCP.Font import (
                Font_FA_Regular,
                Font_FontAspect,
                Font_FontMgr,
                Font_StrictLevel,
                Font_SystemFont,
            )
            from OCP.TCollection import TCollection_AsciiString

            from font_fetcher import fetch_font_remote

            # noinspection PyArgumentList
            _original_font_mgr = Font_FontMgr.GetInstance_s()

            class FontMgrWrapper:
                """
                Wrapper around OCP Font_FontMgr that auto-fetches missing fonts.
                """

                # noinspection PyPep8Naming
                @staticmethod
                def FindFont(*args, **kwargs) -> Font_SystemFont:
                    """
                    Dispatch old/new overloads safely.
                    """
                    if len(args) == 2 and not kwargs:
                        return FontMgrWrapper.find_font_short(*args)

                    return FontMgrWrapper.find_font_full(*args, **kwargs)

                @staticmethod
                def find_font_short(
                    theFontName: TCollection_AsciiString,
                    theFontAspect: Font_FontAspect,
                ) -> Font_SystemFont:
                    """
                    Old OCC overload:
                        FindFont(name, aspect)
                    """
                    return FontMgrWrapper.find_font_full(
                        theFontName,
                        Font_StrictLevel.Font_StrictLevel_Strict,
                        theFontAspect,
                        False,
                    )

                @staticmethod
                def find_font_full(
                    theFontName: TCollection_AsciiString,
                    _theStrictLevel: Font_StrictLevel,
                    theFontAspect: Font_FontAspect,
                    theDoFailMsg: bool,
                ) -> Font_SystemFont:
                    """
                    New OCC overload:
                        FindFont(name, strictLevel, aspect, failMsg)
                    """
                    font_name_orig = theFontName.ToCString()
                    font_name = renames.get(font_name_orig, font_name_orig)

                    font_name_debug = (
                        f"{font_name} (renamed from {font_name_orig})"
                        if font_name != font_name_orig
                        else font_name_orig
                    )

                    logger.debug(
                        f"Trying to find font: {font_name_debug}, "
                        f"aspect: {theFontAspect}"
                    )

                    # Disable OCC fallback aliases.
                    strict_level = Font_StrictLevel.Font_StrictLevel_Strict

                    # IMPORTANT:
                    # Use renamed font name for lookup.
                    font_t = _original_font_mgr.FindFont(
                        TCollection_AsciiString(font_name),
                        strict_level,
                        theFontAspect,
                        theDoFailMsg,
                    )

                    if font_t is not None:
                        logger.debug(f"Found existing font: {font_name_debug}")
                        return font_t

                    style = aspect_to_style.get(
                        theFontAspect,
                        "Regular",
                    )

                    font_path = fetch_font_cached(
                        font_name,
                        style,
                    )

                    if font_path is None:
                        logger.info(
                            f"Font '{font_name}' with style '{style}' "
                            f"not found locally. Attempting remote fetch..."
                        )

                        try:
                            font_path = fetch_font_remote(
                                font_name,
                                style,
                                exact_match,
                            )
                        except FileNotFoundError:
                            logger.warning(
                                f"Could not fetch font '{font_name}' "
                                f"style '{style}'"
                            )

                            if fail_on_not_found:
                                raise

                            return None

                    # IMPORTANT:
                    # Register fetched font.
                    if font_path is not None:
                        font_path = Path(font_path)

                        logger.debug(
                            f"Registering fetched font: {font_path}"
                        )

                        font_t = Font_SystemFont(
                            TCollection_AsciiString(font_name)
                        )

                        # Some OCP versions differ here.
                        # This signature works for newer bindings.
                        font_t.SetFontPath(
                            theFontAspect,
                            TCollection_AsciiString(
                                str(font_path.absolute())
                            ),
                        )

                        _original_font_mgr.RegisterFont(font_t, True)

                        # Re-query after registration to ensure
                        # internal structures are updated.
                        font_t = _original_font_mgr.FindFont(
                            TCollection_AsciiString(font_name),
                            strict_level,
                            theFontAspect,
                            theDoFailMsg,
                        )

                        logger.debug(
                            f"Successfully registered font: {font_name}"
                        )

                    return font_t

                def __getattr__(self, name):
                    return getattr(_original_font_mgr, name)

            _wrapper_instance = FontMgrWrapper()

            Font_FontMgr.GetInstance_s = lambda: _wrapper_instance

            logger.info(
                "Patched OCP Font_FontMgr with auto-download hook."
            )

        except ImportError as err_import:
            logger.warning(
                f"Import error ({err_import}). "
                f"Do you have cadquery-ocp installed?"
            )


# noinspection PyUnresolvedReferences
def uninstall_ocp_font_hook():
    """
    Uninstall the OCP.Font_FontMgr patch.
    """
    global _original_font_mgr
    global _wrapper_instance

    with _font_hook_lock:
        if _original_font_mgr is None:
            logger.info("No OCP Font_FontMgr patch to uninstall.")
            return

        from OCP.Font import Font_FontMgr

        original_mgr = _original_font_mgr

        # Restore original getter.
        Font_FontMgr.GetInstance_s = lambda: original_mgr

        # Reset font DB.
        # NOTE:
        # This clears all runtime font registrations,
        # not just fonts added by this hook.
        original_mgr.ClearFontDataBase()
        original_mgr.InitFontDataBase()

        _original_font_mgr = None
        _wrapper_instance = None

        logger.info("Uninstalled OCP Font_FontMgr patch.")
