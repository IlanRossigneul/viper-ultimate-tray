from collections.abc import Callable
from pathlib import Path

from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QMenu


def create_dpi_stage_menu(
    stage_menu: QMenu,
    stages: list[int],
    icon_dir: Path,
    callback: Callable[[int], None],
) -> list[QAction]:
    stage_items: list[QAction] = []

    stage_group = QActionGroup(stage_menu)
    stage_group.setExclusive(True)

    for index, stage in enumerate(stages, start=1):
        item = QAction(f"{stage:>4}", stage_menu)

        if index == 1:
            item.setIcon(QIcon(str(icon_dir / "slow.svg")))
        elif index == len(stages):
            item.setIcon(QIcon(str(icon_dir / "fast.svg")))

        item.setCheckable(True)

        item.triggered.connect(
            lambda _checked, stage=index: callback(stage),
        )

        stage_group.addAction(item)
        stage_menu.addAction(item)
        stage_items.append(item)

    return stage_items
