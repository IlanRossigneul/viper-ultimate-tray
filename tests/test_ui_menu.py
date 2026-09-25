from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from config.paths import MENU_BATTERY_ICON_DIR, MENU_ICON_DIR, MENU_LOG_ICON_DIR
from ui.menu import create_menu, create_menu_item


def _get_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_create_menu_item_creates_action_without_icon() -> None:
    _get_app()

    action = create_menu_item(text="Test")

    assert isinstance(action, QAction)
    assert action.text() == "Test"
    assert action.icon().isNull() is True


def test_create_menu_item_creates_action_with_icon() -> None:
    _get_app()

    action = create_menu_item(
        MENU_ICON_DIR / "mouse.svg",
        "Test",
    )

    assert action.text() == "Test"
    assert action.icon().isNull() is False


def test_create_menu_builds_expected_menu_structure() -> None:
    _get_app()

    widgets = create_menu(
        MENU_ICON_DIR,
        MENU_BATTERY_ICON_DIR,
        MENU_LOG_ICON_DIR,
        "Razer Viper Ultimate",
    )

    assert widgets.name_item.text() == "Razer Viper Ultimate"
    assert widgets.battery_item.text() == ""
    assert widgets.dpi_item.text() == ""
    assert widgets.stage_item.text() == ""
    assert widgets.idle_item.text() == ""
    assert widgets.low_battery_item.text() == ""

    assert widgets.stage_item.menu() is widgets.stage_menu
    assert widgets.idle_item.menu() is widgets.idle_menu
    assert widgets.low_battery_item.menu() is widgets.low_battery_menu
    assert widgets.logs_item.menu() is not None

    assert widgets.stage_items == []
    assert widgets.idle_items == []
    assert widgets.low_battery_items == []

    assert widgets.menu.actions() == [
        widgets.name_item,
        widgets.menu.actions()[1],
        widgets.battery_item,
        widgets.menu.actions()[3],
        widgets.dpi_item,
        widgets.stage_item,
        widgets.menu.actions()[6],
        widgets.idle_item,
        widgets.low_battery_item,
        widgets.menu.actions()[9],
        widgets.logs_item,
        widgets.menu.actions()[11],
        widgets.polychromatic_action,
        widgets.input_remapper_action,
    ]


def test_create_menu_builds_log_submenu() -> None:
    _get_app()

    widgets = create_menu(
        MENU_ICON_DIR,
        MENU_BATTERY_ICON_DIR,
        MENU_LOG_ICON_DIR,
        "Razer Viper Ultimate",
    )

    assert widgets.logs_item.text() == "Journaux"
    assert widgets.battery_logger_action.text() == "Enregistreur batterie"

    assert widgets.logs_item.menu().actions() == [
        widgets.battery_logger_action,
    ]


def test_create_menu_launches_polychromatic(monkeypatch) -> None:
    _get_app()

    calls = []

    def fake_popen(command, *, start_new_session):
        calls.append((command, start_new_session))

    monkeypatch.setattr(
        "ui.menu.subprocess.Popen",
        fake_popen,
    )

    widgets = create_menu(
        MENU_ICON_DIR,
        MENU_BATTERY_ICON_DIR,
        MENU_LOG_ICON_DIR,
        "Razer Viper Ultimate",
    )

    assert widgets.polychromatic_action.text() == "Ouvrir Polychromatic"

    widgets.polychromatic_action.trigger()

    assert calls == [
        (["polychromatic-controller"], True),
    ]


def test_create_menu_launches_input_remapper(monkeypatch) -> None:
    _get_app()

    calls = []

    def fake_popen(command, *, start_new_session):
        calls.append((command, start_new_session))

    monkeypatch.setattr(
        "ui.menu.subprocess.Popen",
        fake_popen,
    )

    widgets = create_menu(
        MENU_ICON_DIR,
        MENU_BATTERY_ICON_DIR,
        MENU_LOG_ICON_DIR,
        "Razer Viper Ultimate",
    )

    assert widgets.input_remapper_action.text() == "Ouvrir Input Remapper"

    widgets.input_remapper_action.trigger()

    assert calls == [
        (["input-remapper-gtk"], True),
    ]
