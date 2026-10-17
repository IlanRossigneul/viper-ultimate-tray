from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import QApplication, QMenu

from config.paths import MENU_ICON_DIR
from razer.mouse_state import DPIStage
from ui.dpi_menu import create_dpi_stage_menu, update_dpi_stage_menu


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


def test_update_dpi_stage_menu_rebuilds_items_to_match_stages() -> None:
    _get_app()

    menu = QMenu()
    stage_items = []

    stage_items.extend(
        create_dpi_stage_menu(
            menu,
            [
                DPIStage(400),
                DPIStage(800),
                DPIStage(1600),
                DPIStage(2400),
                DPIStage(3200),
            ],
            MENU_ICON_DIR,
            lambda _: None,
        )
    )

    update_dpi_stage_menu(
        menu,
        stage_items,
        [
            DPIStage(400),
            DPIStage(800),
            DPIStage(1600),
            DPIStage(2400),
        ],
        MENU_ICON_DIR,
        lambda _: None,
    )

    assert len(stage_items) == 4
    assert menu.actions() == stage_items
    assert [item.text() for item in stage_items] == [
        "  400",
        "  800",
        " 1600",
        " 2400",
    ]


def test_update_dpi_stage_menu_does_not_rebuild_unchanged_stages() -> None:
    app = _get_app()
    menu = QMenu()
    stages = [DPIStage(400), DPIStage(800), DPIStage(1600)]
    items = create_dpi_stage_menu(menu, stages, MENU_ICON_DIR, lambda _: None)
    original_items = list(items)
    original_groups = menu.findChildren(QActionGroup)

    for _ in range(250):
        update_dpi_stage_menu(
            menu,
            items,
            stages,
            MENU_ICON_DIR,
            lambda _: None,
        )

    app.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    assert items == original_items
    assert menu.actions() == original_items
    assert menu.findChildren(QActionGroup) == original_groups
    assert len(menu.findChildren(QActionGroup)) == 1


def test_update_dpi_stage_menu_releases_replaced_actions_and_groups() -> None:
    app = _get_app()
    menu = QMenu()
    items = create_dpi_stage_menu(
        menu,
        [DPIStage(400), DPIStage(800), DPIStage(1600)],
        MENU_ICON_DIR,
        lambda _: None,
    )
    original_action_count = len(menu.findChildren(type(items[0])))

    for count in range(250):
        update_dpi_stage_menu(
            menu,
            items,
            [DPIStage(400), DPIStage(800 + count * 100), DPIStage(1600)],
            MENU_ICON_DIR,
            lambda _: None,
        )
        app.processEvents()

    app.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    assert len(items) == 3
    assert menu.actions() == items
    assert len(menu.findChildren(QActionGroup)) == 1
    assert len(menu.findChildren(type(items[0]))) == original_action_count
