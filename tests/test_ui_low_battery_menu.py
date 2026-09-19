from pathlib import Path

from PySide6.QtWidgets import QApplication, QMenu

from ui.low_battery_menu import create_low_battery_menu


def _get_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_create_low_battery_menu_creates_expected_items() -> None:
    _get_app()

    menu = QMenu()

    items = create_low_battery_menu(
        menu,
        Path("/tmp/low-battery.svg"),
        lambda _: None,
    )

    assert len(items) == 5
    assert [item.text() for item in items] == [
        "25 %",
        "20 %",
        "15 %",
        "10 %",
        "5 %",
    ]

    assert all(item.isCheckable() for item in items)
    assert menu.actions() == items


def test_create_low_battery_menu_calls_callback_with_threshold() -> None:
    _get_app()

    menu = QMenu()
    callbacks = []

    items = create_low_battery_menu(
        menu,
        Path("/tmp/low-battery.svg"),
        callbacks.append,
    )

    for item in items:
        item.trigger()

    assert callbacks == [25, 20, 15, 10, 5]


def test_create_low_battery_menu_uses_exclusive_selection() -> None:
    _get_app()

    menu = QMenu()

    items = create_low_battery_menu(
        menu,
        Path("/tmp/low-battery.svg"),
        lambda _: None,
    )

    items[0].setChecked(True)
    items[2].setChecked(True)

    assert items[0].isChecked() is False
    assert items[2].isChecked() is True
    assert all(
        not item.isChecked() for index, item in enumerate(items) if index not in {2}
    )
