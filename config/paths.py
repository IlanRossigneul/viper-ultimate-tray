from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOG_DIR = BASE_DIR / "log"

ICON_DIR = BASE_DIR / "icons"

MENU_ICON_DIR = ICON_DIR / "menu"
MENU_BATTERY_ICON_DIR = MENU_ICON_DIR / "battery"
MENU_LOG_ICON_DIR = MENU_ICON_DIR / "log"

TRAY_ICON_DIR = ICON_DIR / "tray"

MODEL_FILE = LOG_DIR / "battery_charge_model.json"
