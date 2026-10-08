from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QApplication

from config.paths import MENU_BATTERY_ICON_DIR, MENU_ICON_DIR, TRAY_ICON_DIR
from razer.mouse_state import ChargingSource, DPIStage, MouseState
from ui.status_view import StatusView


class FakeIndicator:
    def __init__(self) -> None:
        self.icon = None
        self.title = None

    def setIconByPixmap(self, icon) -> None:
        self.icon = icon

    def setTitle(self, title: str) -> None:
        self.title = title


def _get_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _create_action() -> QAction:
    return QAction()


def _create_status_view() -> tuple[StatusView, FakeIndicator]:
    indicator = FakeIndicator()

    name_item = _create_action()
    battery_item = _create_action()
    dpi_item = _create_action()
    dpi_edit_action = _create_action()
    stage_item = _create_action()
    idle_item = _create_action()
    low_battery_item = _create_action()

    stage_group = QActionGroup(stage_item)
    stage_group.setExclusive(True)

    stage_items = [_create_action() for _ in range(3)]

    for item in stage_items:
        item.setCheckable(True)
        stage_group.addAction(item)

    idle_group = QActionGroup(idle_item)
    idle_group.setExclusive(True)

    idle_items = [_create_action() for _ in range(15)]

    for item in idle_items:
        item.setCheckable(True)
        idle_group.addAction(item)

    low_battery_group = QActionGroup(low_battery_item)
    low_battery_group.setExclusive(True)

    low_battery_items = [_create_action() for _ in range(5)]

    for item in low_battery_items:
        item.setCheckable(True)
        low_battery_group.addAction(item)

    view = StatusView(
        indicator=indicator,
        menu_icon_dir=MENU_ICON_DIR,
        tray_icon_dir=TRAY_ICON_DIR,
        menu_battery_icon_dir=MENU_BATTERY_ICON_DIR,
        charge_models={"wired": {}, "wireless": {}},
        name_item=name_item,
        battery_item=battery_item,
        dpi_item=dpi_item,
        dpi_edit_action=dpi_edit_action,
        stage_item=stage_item,
        idle_item=idle_item,
        low_battery_item=low_battery_item,
        stage_items=stage_items,
        idle_items=idle_items,
        low_battery_items=low_battery_items,
    )

    return view, indicator


def _create_connected_state(
    *,
    battery: float | None = 30.8,
    charging: bool | None = False,
    charging_source: ChargingSource | None = ChargingSource.WIRED,
) -> MouseState:
    return MouseState(
        connected=True,
        device_name="Razer Viper Ultimate",
        battery=battery,
        charging=charging,
        charging_source=charging_source,
        dpi=(1600, 1600),
        active_stage=2,
        stages=[
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ],
        idle_minutes=5,
        low_battery_threshold=15,
    )


def test_show_disconnected_updates_status_and_disables_actions() -> None:
    _get_app()

    view, indicator = _create_status_view()

    view.show_disconnected()

    assert indicator.icon is not None
    assert indicator.icon.isNull() is False
    assert indicator.title == "Razer Viper Ultimate déconnectée"

    assert view.name_item.text() == "Razer Viper Ultimate déconnectée"
    assert view.battery_item.text() == "Batterie : —"
    assert view.dpi_item.text() == "DPI : —"
    assert view.stage_item.text() == "Plage active : —"
    assert view.idle_item.text() == "Hibernation : —"
    assert view.low_battery_item.text() == "Basse consommation : —"

    assert not view.battery_item.isEnabled()
    assert not view.dpi_item.isEnabled()
    assert not view.dpi_edit_action.isEnabled()
    assert not view.stage_item.isEnabled()
    assert not view.idle_item.isEnabled()
    assert not view.low_battery_item.isEnabled()

    assert all(not item.isEnabled() for item in view.stage_items)
    assert all(not item.isEnabled() for item in view.idle_items)
    assert all(not item.isEnabled() for item in view.low_battery_items)


def test_show_connected_without_battery_shows_unavailable_battery() -> None:
    _get_app()

    view, indicator = _create_status_view()
    state = _create_connected_state(battery=None)

    view.show_connected(state)

    assert indicator.icon is not None
    assert indicator.icon.isNull() is False
    assert view.name_item.text() == "Razer Viper Ultimate"
    assert view.battery_item.text() == "Batterie : —"


def test_show_connected_updates_status_from_mouse_state() -> None:
    _get_app()

    view, indicator = _create_status_view()
    state = _create_connected_state()

    view.show_connected(state)

    assert indicator.icon is not None
    assert indicator.icon.isNull() is False
    assert indicator.title == "Razer Viper Ultimate — 30 %"

    assert view.name_item.text() == "Razer Viper Ultimate"
    assert view.battery_item.text() == "Batterie : 30 %"
    assert view.dpi_item.text() == "DPI : 1600"
    assert view.stage_item.text() == "Plage DPI : 2 / 3"
    assert view.idle_item.text() == "Hibernation : 5 min"
    assert view.low_battery_item.text() == "Basse consommation : 15 %"

    assert view.battery_item.isEnabled()
    assert view.dpi_item.isEnabled()
    assert view.dpi_edit_action.isEnabled()
    assert view.stage_item.isEnabled()
    assert view.idle_item.isEnabled()
    assert view.low_battery_item.isEnabled()

    assert all(item.isEnabled() for item in view.stage_items)
    assert all(item.isEnabled() for item in view.idle_items)
    assert all(item.isEnabled() for item in view.low_battery_items)

    assert view.stage_items[0].text() == "  800"
    assert view.stage_items[1].text() == " 1600"
    assert view.stage_items[2].text() == " 3200"

    assert view.stage_items[0].isChecked() is False
    assert view.stage_items[1].isChecked() is True
    assert view.stage_items[2].isChecked() is False

    assert view.idle_items[10].isChecked() is True
    assert view.low_battery_items[2].isChecked() is True


def test_show_connected_updates_selection_for_current_values() -> None:
    _get_app()

    view, _ = _create_status_view()

    state = _create_connected_state()
    view.show_connected(state)

    state.idle_minutes = 15
    state.low_battery_threshold = 25
    state.active_stage = 3
    state.stages = [
        DPIStage(800),
        DPIStage(1600),
        DPIStage(3200),
    ]

    view.show_connected(state)

    assert view.stage_items[0].isChecked() is False
    assert view.stage_items[1].isChecked() is False
    assert view.stage_items[2].isChecked() is True

    assert view.idle_items[0].isChecked() is True
    assert all(not item.isChecked() for item in view.idle_items[1:])

    assert view.low_battery_items[0].isChecked() is True
    assert all(not item.isChecked() for item in view.low_battery_items[1:])


def test_show_connected_appends_charge_estimation_when_charging(
    monkeypatch,
) -> None:
    _get_app()

    view, _ = _create_status_view()
    state = _create_connected_state(
        battery=50.5,
        charging=True,
        charging_source=ChargingSource.WIRED,
    )

    monkeypatch.setattr(
        "ui.status_view.get_charge_estimation",
        lambda battery, source, models: "2 h environ avant pleine recharge",
    )

    view.show_connected(state)

    assert (
        view.battery_item.text()
        == "Batterie : 50 % (2 h environ avant pleine recharge)"
    )


def test_show_connected_does_not_append_missing_charge_estimation(
    monkeypatch,
) -> None:
    _get_app()

    view, _ = _create_status_view()
    state = _create_connected_state(
        battery=50.5,
        charging=True,
        charging_source=ChargingSource.WIRED,
    )

    monkeypatch.setattr(
        "ui.status_view.get_charge_estimation",
        lambda battery, source, models: None,
    )

    view.show_connected(state)

    assert view.battery_item.text() == "Batterie : 50 %"
