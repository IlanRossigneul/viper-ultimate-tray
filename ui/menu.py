import subprocess
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu


@dataclass(slots=True)
class MenuWidgets:
    menu: QMenu

    name_item: QAction
    battery_item: QAction
    dpi_item: QAction
    stage_item: QAction
    idle_item: QAction
    low_battery_item: QAction

    stage_menu: QMenu
    stage_items: list[QAction]

    idle_menu: QMenu
    idle_items: list[QAction]

    low_battery_menu: QMenu
    low_battery_items: list[QAction]

    logs_item: QAction
    battery_logger_start_action: QAction
    battery_logger_stop_action: QAction

    polychromatic_action: QAction
    input_remapper_action: QAction


def create_menu_item(icon_path: Path | None = None, text: str = "") -> QAction:
    action = QAction()

    if icon_path is not None:
        action.setIcon(QIcon(str(icon_path)))

    action.setText(text)

    return action


def add_separator(menu: QMenu) -> None:
    menu.addSeparator()


def create_menu(
    menu_icon_dir: Path,
    menu_battery_icon_dir: Path,
    menu_log_icon_dir: Path,
    device_name: str,
) -> MenuWidgets:
    menu = QMenu()

    name_item = create_menu_item(menu_icon_dir / "mouse.svg", device_name)

    battery_item = create_menu_item(menu_battery_icon_dir / "battery-4.svg")

    dpi_item = create_menu_item(menu_icon_dir / "dpi.svg")

    stage_item = create_menu_item(menu_icon_dir / "stages-dpi.svg")

    idle_item = create_menu_item(menu_icon_dir / "hibernation.svg")

    low_battery_item = create_menu_item(menu_icon_dir / "low_battery.svg")

    stage_menu = QMenu()

    stage_item.setMenu(stage_menu)

    stage_items: list[QAction] = []

    idle_menu = QMenu()

    idle_item.setMenu(idle_menu)

    idle_items: list[QAction] = []

    low_battery_menu = QMenu()

    low_battery_item.setMenu(low_battery_menu)

    low_battery_items: list[QAction] = []

    logs_item = create_menu_item(menu_log_icon_dir / "logs.svg", "Journaux")

    logs_menu = QMenu()

    logs_item.setMenu(logs_menu)

    battery_logger_start_action = create_menu_item(
        menu_log_icon_dir / "start.svg",
        "Démarrer",
    )

    battery_logger_stop_action = create_menu_item(
        menu_log_icon_dir / "stop.svg",
        "Arrêter",
    )

    polychromatic_action = create_menu_item(
        menu_icon_dir / "polychromatic.svg",
        "Ouvrir Polychromatic",
    )

    polychromatic_action.triggered.connect(
        lambda: subprocess.Popen(["polychromatic-controller"], start_new_session=True)
    )

    input_remapper_action = create_menu_item(
        menu_icon_dir / "input-remapper.svg",
        "Ouvrir Input Remapper",
    )

    input_remapper_action.triggered.connect(
        lambda: subprocess.Popen(["input-remapper-gtk"], start_new_session=True)
    )

    menu.addAction(name_item)

    add_separator(menu)

    menu.addAction(battery_item)

    add_separator(menu)

    menu.addAction(dpi_item)
    menu.addAction(stage_item)

    add_separator(menu)

    menu.addAction(idle_item)
    menu.addAction(low_battery_item)

    add_separator(menu)

    logs_menu.addAction(battery_logger_start_action)
    logs_menu.addAction(battery_logger_stop_action)

    menu.addAction(logs_item)

    add_separator(menu)

    menu.addAction(polychromatic_action)
    menu.addAction(input_remapper_action)

    return MenuWidgets(
        menu=menu,
        name_item=name_item,
        battery_item=battery_item,
        dpi_item=dpi_item,
        stage_item=stage_item,
        idle_item=idle_item,
        low_battery_item=low_battery_item,
        stage_menu=stage_menu,
        stage_items=stage_items,
        idle_menu=idle_menu,
        idle_items=idle_items,
        low_battery_menu=low_battery_menu,
        low_battery_items=low_battery_items,
        logs_item=logs_item,
        battery_logger_start_action=battery_logger_start_action,
        battery_logger_stop_action=battery_logger_stop_action,
        polychromatic_action=polychromatic_action,
        input_remapper_action=input_remapper_action,
    )
