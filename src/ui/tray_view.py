from pathlib import Path

from KStatusNotifierItem import KStatusNotifierItem
from PySide6.QtGui import QPixmap


def create_indicator(icon_dir: Path) -> KStatusNotifierItem:
    indicator = KStatusNotifierItem()

    indicator.setIconByPixmap(QPixmap(str(icon_dir / "mouse.svg")))

    indicator.setTitle("Razer Viper Ultimate")
    indicator.setToolTipTitle("Razer Viper Ultimate")
    indicator.setIsMenu(True)
    indicator.setStandardActionsEnabled(True)
    indicator.setStatus(KStatusNotifierItem.ItemStatus.Active)

    return indicator
