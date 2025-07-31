from typing import Dict, Optional

from font_fetcher import fetch_font_cached
from font_fetcher.misc import logger

_original_font_mgr = None
aspect_to_style: Dict[int, str] = {1: "Bold", 2: "Italic", 3: "Bold Italic"}  # From OCP.Font_FontAspect


def install_ocp_font_hook(renames: Optional[Dict[str, str]] = None, exact_match: bool = True):
    """Install the OCP.Font_FontMgr patch to auto-download missing fonts."""
    if renames is None:
        renames = {'Arial': 'DejaVu Sans'}
    global _original_font_mgr
    if _original_font_mgr is not None:
        logger.info("OCP Font_FontMgr patch already installed. Skipping installation.")
        return
    try:
        from OCP.Font import Font_FontMgr, Font_SystemFont, Font_FA_Regular, Font_StrictLevel, Font_FontAspect
        from OCP.TCollection import TCollection_AsciiString
        from font_fetcher import fetch_font_remote

        # noinspection PyArgumentList
        _original_font_mgr = Font_FontMgr.GetInstance_s()
        Font_FontMgr.GetInstance_s = lambda: FontMgrWrapper()

        class FontMgrWrapper:
            # noinspection PyPep8Naming
            @staticmethod
            def FindFont(*args, **kwargs) -> Font_SystemFont:
                if len(args) + len(kwargs) == 2:
                    # If only two arguments are passed, assume it's the old FindFont signature
                    return FontMgrWrapper.find_font_short(*args, **kwargs)
                else:
                    # If three arguments are passed, assume it's the new FindFont signature
                    return FontMgrWrapper.find_font_full(*args, **kwargs)

            @staticmethod
            def find_font_short(theFontName: TCollection_AsciiString,
                                theFontAspect: Font_FontAspect) -> Font_SystemFont:
                """Find font with the given name and aspect, using strict level."""
                return FontMgrWrapper.find_font_full(theFontName, Font_StrictLevel.Font_StrictLevel_Strict,
                                                     theFontAspect, False)

            @staticmethod
            def find_font_full(theFontName: TCollection_AsciiString, _theStrictLevel: Font_StrictLevel,
                               theFontAspect: Font_FontAspect, theDoFailMsg: bool) -> Font_SystemFont:
                font_name_orig = theFontName.ToCString()
                font_name = renames.get(font_name_orig, font_name_orig)
                font_name_debug = f"{font_name} (renamed from {font_name_orig})" if font_name != font_name_orig else font_name_orig
                logger.debug(f"Trying to find font: {font_name_debug}, kind: {theFontAspect}")
                theStrictLevel = Font_StrictLevel.Font_StrictLevel_Strict  # Disable fallbacks or aliases
                font_t = _original_font_mgr.FindFont(theFontName, theStrictLevel, theFontAspect, theDoFailMsg)
                if font_t is None:
                    style = aspect_to_style.get(theFontAspect, "Regular")
                    font_path = fetch_font_cached(font_name, style)
                    if font_path is None:
                        logger.info(f"Font '{font_name}' with style '{style}' not found. Attempting to fetch it...")
                        font_path = fetch_font_remote(font_name, style)

                    logger.debug(f"Fetched font: {font_path}. Returning it...")
                    font_t = Font_SystemFont(TCollection_AsciiString(font_name))
                    font_t.SetFontPath(theFontAspect, TCollection_AsciiString(str(font_path.absolute())))
                    _original_font_mgr.RegisterFont(font_t, True)
                    # logger.debug(f"Font registered successfully: {font_name}. Running original FindFont again...")
                return font_t

            def __getattr__(self, name):
                return getattr(_original_font_mgr, name)

        logger.info("Patched OCP Font_FontMgr with auto-download hook.")
    except ImportError as err_import:
        logger.warning(f"Import error ({err_import}). Do you have cadquery-ocp installed?")


# noinspection PyUnresolvedReferences
def uninstall_ocp_font_hook():
    """Uninstall the OCP.Font_FontMgr.FindFont patch."""
    global _original_font_mgr
    if _original_font_mgr:
        from OCP.Font import Font_FontMgr
        # No way to remove only the added fonts, so reset the Font_FontMgr instance
        _original_font_mgr_tmp = _original_font_mgr
        _original_font_mgr_tmp.ClearFontDataBase()
        _original_font_mgr_tmp.InitFontDataBase()
        Font_FontMgr.GetInstance_s = lambda: _original_font_mgr_tmp
        _original_font_mgr = None
        logger.info("Uninstalled OCP Font_FontMgr patch.")
    else:
        logger.info("No OCP Font_FontMgr patch to uninstall.")
