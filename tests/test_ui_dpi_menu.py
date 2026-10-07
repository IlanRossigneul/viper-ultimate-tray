from PySide6.QtWidgets import QApplication, QMenu

from config.paths import MENU_ICON_DIR
from razer.mouse_state import DPIStage
from ui.dpi_menu import create_dpi_stage_menu


def _get_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_create_dpi_stage_menu_creates_expected_items() -> None:
    _get_app()

    menu = QMenu()
    stages = [
        DPIStage(800),
        DPIStage(1600),
        DPIStage(3200),
    ]
    icon_dir = MENU_ICON_DIR
    callbacks = []

    items = create_dpi_stage_menu(
        menu,
        stages,
        icon_dir,
        callbacks.append,
    )

    assert len(items) == 3
    assert [item.text() for item in items] == [
        "  800",
        " 1600",
        " 3200",
    ]

    assert all(item.isCheckable() for item in items)
    assert menu.actions() == items


def test_create_dpi_stage_menu_assigns_first_and_last_icons() -> None:
    _get_app()

    menu = QMenu()

    items = create_dpi_stage_menu(
        menu,
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ],
        MENU_ICON_DIR,
        lambda _: None,
    )

    assert items[0].icon().isNull() is False
    assert items[2].icon().isNull() is False
    assert items[1].icon().isNull() is True


def test_create_dpi_stage_menu_calls_callback_with_stage_number() -> None:
    _get_app()

    menu = QMenu()
    callbacks = []

    items = create_dpi_stage_menu(
        menu,
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ],
        MENU_ICON_DIR,
        callbacks.append,
    )

    for item in items:
        item.trigger()

    assert callbacks == [1, 2, 3]


def test_create_dpi_stage_menu_uses_exclusive_selection() -> None:
    _get_app()

    menu = QMenu()

    items = create_dpi_stage_menu(
        menu,
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ],
        MENU_ICON_DIR,
        lambda _: None,
    )

    items[0].setChecked(True)
    items[1].setChecked(True)

    assert items[0].isChecked() is False
    assert items[1].isChecked() is True
    assert items[2].isChecked() is False


def test_create_dpi_stage_menu_with_single_stage_uses_slow_icon() -> None:
    _get_app()

    menu = QMenu()

    items = create_dpi_stage_menu(
        menu,
        [DPIStage(1600)],
        MENU_ICON_DIR,
        lambda _: None,
    )

    assert len(items) == 1
    assert items[0].icon().isNull() is False
