from pathlib import Path

from PySide6.QtGui import QPixmap

from KStatusNotifierItem import KStatusNotifierItem


def create_indicator(icon_dir: Path) -> KStatusNotifierItem:
    indicator = KStatusNotifierItem()

    indicator.setIconByPixmap(QPixmap(str(icon_dir / "mouse.svg")))

    indicator.setTitle("Razer Viper Ultimate")
    indicator.setToolTipTitle("Razer Viper Ultimate")
    indicator.setIsMenu(True)
    indicator.setStandardActionsEnabled(True)
    indicator.setStatus(KStatusNotifierItem.ItemStatus.Active)

    return indicator