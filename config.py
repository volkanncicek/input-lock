import sys
from pathlib import Path


def get_resource_path(relative_path):
  """Get absolute path to resource, works for dev and for PyInstaller"""
  try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = sys._MEIPASS
  except Exception:
    base_path = Path(__file__).parent

  return Path(base_path) / relative_path


ASSETS_DIR = get_resource_path("assets")
FONT_FAMILY = "Segoe UI"


THEME_CONFIG = {
  "dark": {
    "background": "#2D2D2D",
    "text_color": "#FFFFFF",
    "text_muted": "#BBBBBB",
    "button_primary_bg": "#0078D4",
    "button_primary_fg": "white",
    "button_primary_hover": "#108ee9",
    "button_secondary_bg": "#555555",
    "button_secondary_fg": "white",
    "button_secondary_hover": "#6A6A6A",
    "overlay_bg": "#202020",
  },
  "light": {
    "background": "#FFFFFF",
    "text_color": "#000000",
    "text_muted": "#555555",
    "button_primary_bg": "#0078D4",
    "button_primary_fg": "white",
    "button_primary_hover": "#108ee9",
    "button_secondary_bg": "#555555",
    "button_secondary_fg": "white",
    "button_secondary_hover": "#6A6A6A",
    "overlay_bg": "#F0F0F0",
  },
}
