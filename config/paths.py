from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ICON_DIR = BASE_DIR / "icons"

MENU_ICON_DIR = ICON_DIR / "menu"
MENU_BATTERY_ICON_DIR = MENU_ICON_DIR / "battery"

TRAY_ICON_DIR = ICON_DIR / "tray"

MODEL_FILE = BASE_DIR / "log" / "battery_charge_model.json"