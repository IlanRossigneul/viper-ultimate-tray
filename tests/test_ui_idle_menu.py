from pathlib import Path

from PySide6.QtWidgets import QApplication, QMenu

from ui.idle_menu import create_idle_time_menu


def _get_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_create_idle_time_menu_creates_items_from_15_to_1_minute() -> None:
    _get_app()

    menu = QMenu()

    items = create_idle_time_menu(
        menu,
        Path("/tmp/hibernation.svg"),
        lambda _: None,
    )

    assert len(items) == 15
    assert [item.text() for item in items] == [
        "15 minutes",
        "14 minutes",
        "13 minutes",
        "12 minutes",
        "11 minutes",
        "10 minutes",
        "9 minutes",
        "8 minutes",
        "7 minutes",
        "6 minutes",
        "5 minutes",
        "4 minutes",
        "3 minutes",
        "2 minutes",
        "1 minute",
    ]

    assert all(item.isCheckable() for item in items)
    assert menu.actions() == items


def test_create_idle_time_menu_calls_callback_with_minutes() -> None:
    _get_app()

    menu = QMenu()
    callbacks = []

    items = create_idle_time_menu(
        menu,
        Path("/tmp/hibernation.svg"),
        callbacks.append,
    )

    for item in items:
        item.trigger()

    assert callbacks == list(range(15, 0, -1))


def test_create_idle_time_menu_uses_exclusive_selection() -> None:
    _get_app()

    menu = QMenu()

    items = create_idle_time_menu(
        menu,
        Path("/tmp/hibernation.svg"),
        lambda _: None,
    )

    items[0].setChecked(True)
    items[5].setChecked(True)

    assert items[0].isChecked() is False
    assert items[5].isChecked() is True
    assert all(
        not item.isChecked() for index, item in enumerate(items) if index not in {5}
    )
