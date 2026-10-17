from collections.abc import Callable
from pathlib import Path

from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QMenu

from razer.mouse_state import DPIStage


def update_dpi_stage_menu(
    stage_menu: QMenu,
    stage_items: list[QAction],
    stages: list[DPIStage],
    icon_dir: Path,
    callback: Callable[[int], None],
) -> None:
    """Update the DPI stage menu only when the stages have changed."""
    stage_values = [stage.dpi for stage in stages]

    if stage_items and [item.data() for item in stage_items] == stage_values:
        return

    stage_group = stage_menu.findChild(QActionGroup, "dpiStageGroup")
    if stage_group is None:
        stage_group = QActionGroup(stage_menu)
        stage_group.setObjectName("dpiStageGroup")
        stage_group.setExclusive(True)

    for item in stage_items:
        stage_menu.removeAction(item)
        stage_group.removeAction(item)
        item.deleteLater()

    stage_items.clear()

    for index, stage in enumerate(stages, start=1):
        item = QAction(f"{stage.dpi:>5}", stage_menu)

        if index == 1:
            item.setIcon(QIcon(str(icon_dir / "slow.svg")))
        elif index == len(stages):
            item.setIcon(QIcon(str(icon_dir / "fast.svg")))

        item.setCheckable(True)
        item.setData(stage.dpi)

        item.triggered.connect(
            lambda _checked, stage=index: callback(stage),
        )

        stage_group.addAction(item)
        stage_menu.addAction(item)
        stage_items.append(item)


def create_dpi_stage_menu(
    stage_menu: QMenu,
    stages: list[DPIStage],
    icon_dir: Path,
    callback: Callable[[int], None],
) -> list[QAction]:
    """Create the DPI stage menu."""
    stage_items: list[QAction] = []

    update_dpi_stage_menu(
        stage_menu,
        stage_items,
        stages,
        icon_dir,
        callback,
    )

    return stage_items
