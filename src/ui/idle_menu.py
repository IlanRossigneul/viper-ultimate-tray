from collections.abc import Callable
from pathlib import Path

from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QMenu


def create_idle_time_menu(
    idle_menu: QMenu,
    icon_path: Path,
    callback: Callable[[int], None],
) -> list[QAction]:
    idle_items: list[QAction] = []

    idle_group = QActionGroup(idle_menu)
    idle_group.setExclusive(True)

    for minutes in range(15, 0, -1):
        text = f"{minutes} minutes" if minutes > 1 else "1 minute"

        item = QAction(QIcon(str(icon_path)), text, idle_menu)
        item.setCheckable(True)

        idle_group.addAction(item)
        idle_menu.addAction(item)

        item.triggered.connect(
            lambda _checked, value=minutes: callback(value),
        )

        idle_items.append(item)

    return idle_items
