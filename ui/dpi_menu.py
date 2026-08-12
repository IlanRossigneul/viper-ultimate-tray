from collections.abc import Callable

from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMenu

from razer.mouse_state import DPIStage


def create_dpi_stage_menu(
    stage_menu: QMenu,
    stages: list[DPIStage],
    callback: Callable[[int], None],
) -> list[QAction]:
    stage_items: list[QAction] = []

    stage_group = QActionGroup(stage_menu)
    stage_group.setExclusive(True)

    for index, stage in enumerate(stages, start=1):
        item = QAction(f"{stage.x:>4}", stage_menu)

        item.setCheckable(True)

        item.triggered.connect(lambda _checked, stage=index: callback(stage))

        stage_group.addAction(item)
        stage_menu.addAction(item)
        stage_items.append(item)

    return stage_items