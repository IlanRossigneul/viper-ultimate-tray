from collections.abc import Callable
from pathlib import Path

from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QMenu


def create_low_battery_menu(
    low_battery_menu: QMenu,
    icon_path: Path,
    callback: Callable[[int], None],
) -> list[QAction]:
    low_battery_items: list[QAction] = []

    low_battery_group = QActionGroup(low_battery_menu)
    low_battery_group.setExclusive(True)

    for threshold in range(25, 4, -5):
        item = QAction(
            QIcon(str(icon_path)),
            f"{threshold} %",
            low_battery_menu,
        )
        item.setCheckable(True)

        low_battery_group.addAction(item)
        low_battery_menu.addAction(item)

        item.triggered.connect(
            lambda _checked, value=threshold: callback(value),
        )

        low_battery_items.append(item)

    return low_battery_items
