from types import SimpleNamespace

import pytest

import razer.mouse_state
from razer.mouse_state import (
    ChargingSource,
    DPIStage,
    MousePollingSession,
    get_mouse_state,
)


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
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
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


def test_polling_session_reuses_manager_and_caches_stable_values(monkeypatch) -> None:
    calls = {
        "manager": 0,
        "battery": 0,
        "charging": 0,
        "dpi": 0,
        "stages": 0,
        "idle": 0,
        "threshold": 0,
    }

    class PollingMouse:
        name = "Razer Viper Ultimate"

        def __init__(self) -> None:
            self.active_stage = 1
            self._dbus_interfaces = {
                "power": SimpleNamespace(
                    getBattery=lambda: (
                        calls.__setitem__(
                            "battery",
                            calls["battery"] + 1,
                        )
                        or 60.0
                    ),
                ),
            }

        @property
        def is_charging(self):
            calls["charging"] += 1
            return False

        @property
        def dpi(self):
            calls["dpi"] += 1
            return (800, 500)

        @property
        def dpi_stages(self):
            calls["stages"] += 1
            return (self.active_stage, [(400, 400), (800, 800)])

        def get_idle_time(self):
            calls["idle"] += 1
            return 300

        def get_low_battery_threshold(self):
            calls["threshold"] += 1
            return 15

    mouse = PollingMouse()

    def create_manager():
        calls["manager"] += 1
        return object()

    monkeypatch.setattr(
        razer.mouse_state,
        "create_device_manager",
        create_manager,
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

    session = MousePollingSession()

    first_state = session.get_state()
    mouse.active_stage = 2
    second_state = session.get_state()

    assert first_state.connected
    assert first_state.dpi == (800, 500)
    assert second_state.connected
    assert second_state.dpi == (800, 800)
    assert session.connection_generation == 1
    assert calls == {
        "manager": 1,
        "battery": 2,
        "charging": 2,
        "dpi": 1,
        "stages": 2,
        "idle": 1,
        "threshold": 1,
    }


def test_polling_session_refreshes_dpi_after_reconnection(monkeypatch) -> None:
    mouse = _create_mouse(
        dpi=(1600, 1600),
        dpi_stages=(2, [(400, 400), (800, 800), (1600, 1600)]),
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

    session = MousePollingSession()
    first_state = session.get_state()
    assert first_state.dpi == (1600, 1600)
    assert first_state.active_stage == 2

    # Simulate the device returning a different current DPI after reconnecting
    # while preserving the same active stage and configured stages.
    session._invalidate()
    mouse.dpi = (800, 200)

    reconnected_state = session.get_state()

    assert reconnected_state.connected
    assert reconnected_state.dpi == (800, 200)
    assert reconnected_state.active_stage == 2
    assert session.connection_generation == 2


def test_polling_session_updates_cached_dpi_and_settings() -> None:
    session = MousePollingSession()
    initial_state = razer.mouse_state.MouseState(
        connected=True,
        device_name="Razer Viper Ultimate",
        battery=60.0,
        charging=False,
        charging_source=ChargingSource.WIRELESS,
        dpi=(800, 500),
        active_stage=1,
        stages=[DPIStage(400), DPIStage(800)],
        idle_minutes=5,
        low_battery_threshold=15,
    )
    session.seed_state(initial_state)

    session.update_dpi((800, 500))
    session.update_dpi_stages([DPIStage(400), DPIStage(800)], 1)
    session.update_dpi((800, 500))
    session.update_idle_minutes(10)
    session.update_low_battery_threshold(20)

    state = session.get_cached_state()

    assert state.dpi == (800, 500)
    assert state.active_stage == 1
    assert state.idle_minutes == 10
    assert state.low_battery_threshold == 20
