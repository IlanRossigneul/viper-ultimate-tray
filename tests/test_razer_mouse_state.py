from types import SimpleNamespace

import pytest

import razer.mouse_state
from razer.mouse_state import ChargingSource, DPIStage, get_mouse_state


def _create_mouse(
    *,
    battery: float = 50.0,
    charging: bool = False,
    name: str = "Razer Viper Ultimate",
    dpi: tuple[int, int] = (1600, 1600),
    dpi_stages: tuple[int, list[tuple[int, int]]] = (
        1,
        [(800, 800), (1600, 1600), (3200, 3200)],
    ),
    idle_seconds: int = 300,
    low_battery_threshold: int = 15,
) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        _dbus_interfaces={"power": SimpleNamespace(getBattery=lambda: battery)},
        is_charging=charging,
        dpi=dpi,
        dpi_stages=dpi_stages,
        get_idle_time=lambda: idle_seconds,
        get_low_battery_threshold=lambda: low_battery_threshold,
    )


def test_get_mouse_state_returns_disconnected_when_device_manager_fails(
    monkeypatch,
) -> None:
    def create_device_manager():
        raise RuntimeError("OpenRazer unavailable")

    monkeypatch.setattr(
        razer.mouse_state,
        "create_device_manager",
        create_device_manager,
    )

    state = get_mouse_state()

    assert state.connected is False
    assert state.device_name is None
    assert state.battery is None
    assert state.charging is None
    assert state.charging_source is None
    assert state.dpi is None
    assert state.active_stage is None
    assert state.stages == []
    assert state.idle_minutes is None
    assert state.low_battery_threshold is None


def test_get_mouse_state_returns_disconnected_when_mouse_is_not_found(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        razer.mouse_state,
        "create_device_manager",
        lambda: object(),
    )
    monkeypatch.setattr(
        razer.mouse_state,
        "find_viper_ultimate_device",
        lambda _: None,
    )

    state = get_mouse_state()

    assert state.connected is False
    assert state.device_name is None
    assert state.battery is None
    assert state.charging is None
    assert state.charging_source is None
    assert state.dpi is None
    assert state.active_stage is None
    assert state.stages == []
    assert state.idle_minutes is None
    assert state.low_battery_threshold is None


@pytest.mark.parametrize(
    ("battery", "charging", "expected_battery"),
    [
        (-1.0, False, None),
        (0.0, False, None),
        (0.0, True, 0),
        (42.5, False, 42.5),
        (100.0, True, 100.0),
    ],
)
def test_get_mouse_state_normalizes_battery(
    monkeypatch,
    battery: float,
    charging: bool,
    expected_battery: float | None,
) -> None:
    mouse = _create_mouse(battery=battery, charging=charging)

    monkeypatch.setattr(
        razer.mouse_state,
        "create_device_manager",
        lambda: object(),
    )
    monkeypatch.setattr(
        razer.mouse_state,
        "find_viper_ultimate_device",
        lambda _: mouse,
    )
    monkeypatch.setattr(
        razer.mouse_state,
        "get_charging_source",
        lambda _: "wireless",
    )

    state = get_mouse_state()

    assert state.connected is True
    assert state.battery == expected_battery
    assert state.charging is charging


def test_get_mouse_state_builds_complete_wireless_state(monkeypatch) -> None:
    mouse = _create_mouse(
        name="Razer Viper Ultimate",
        battery=73.5,
        charging=True,
        dpi=(1600, 1200),
        dpi_stages=(
            2,
            [(800, 800), (1600, 1200), (3200, 3200)],
        ),
        idle_seconds=125,
        low_battery_threshold=20,
    )

    monkeypatch.setattr(
        razer.mouse_state,
        "create_device_manager",
        lambda: object(),
    )
    monkeypatch.setattr(
        razer.mouse_state,
        "find_viper_ultimate_device",
        lambda _: mouse,
    )
    monkeypatch.setattr(
        razer.mouse_state,
        "get_charging_source",
        lambda _: "wireless",
    )

    state = get_mouse_state()

    assert state == razer.mouse_state.MouseState(
        connected=True,
        device_name="Razer Viper Ultimate",
        battery=73.5,
        charging=True,
        charging_source=ChargingSource.WIRELESS,
        dpi=(1600, 1200),
        active_stage=2,
        stages=[
            DPIStage(800, 800),
            DPIStage(1600, 1200),
            DPIStage(3200, 3200),
        ],
        idle_minutes=2,
        low_battery_threshold=20,
    )


def test_get_mouse_state_returns_disconnected_when_reading_state_fails(
    monkeypatch,
) -> None:
    mouse = _create_mouse()

    class FailingMouse:
        def __getattr__(self, name: str):
            if name == "dpi":
                raise RuntimeError("DPI unavailable")
            return getattr(mouse, name)

    mouse = FailingMouse()

    monkeypatch.setattr(
        razer.mouse_state,
        "create_device_manager",
        lambda: object(),
    )
    monkeypatch.setattr(
        razer.mouse_state,
        "find_viper_ultimate_device",
        lambda _: mouse,
    )

    state = get_mouse_state()

    assert state.connected is False
    assert state.battery is None
    assert state.charging is None
    assert state.charging_source is None


def test_get_mouse_state_builds_wired_state(monkeypatch) -> None:
    mouse = _create_mouse(
        name="Razer Viper Ultimate (Wired)",
        battery=100.0,
        charging=False,
    )

    monkeypatch.setattr(
        razer.mouse_state,
        "create_device_manager",
        lambda: object(),
    )
    monkeypatch.setattr(
        razer.mouse_state,
        "find_viper_ultimate_device",
        lambda _: mouse,
    )
    monkeypatch.setattr(
        razer.mouse_state,
        "get_charging_source",
        lambda _: "wired",
    )

    state = get_mouse_state()

    assert state.charging_source is ChargingSource.WIRED
