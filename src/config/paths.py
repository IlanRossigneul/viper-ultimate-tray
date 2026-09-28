from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

BATTERY_LOGS_DIR = BASE_DIR / "battery_logs"

ICON_DIR = BASE_DIR / "icons"

MENU_ICON_DIR = ICON_DIR / "menu"
MENU_BATTERY_ICON_DIR = MENU_ICON_DIR / "battery"
MENU_LOG_ICON_DIR = MENU_ICON_DIR / "log"

QMESSAGEBOX_ICON_DIR = ICON_DIR / "qmessagebox"

TRAY_ICON_DIR = ICON_DIR / "tray"

MODEL_FILE = BATTERY_LOGS_DIR / "battery_charge_model.json"

INSTANCE_LOCK_FILE = BASE_DIR / "viper-ultimate-tray.lock"
