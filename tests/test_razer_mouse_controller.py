from types import SimpleNamespace

import razer.mouse_controller
from razer.mouse_controller import MouseController


def _create_controller(monkeypatch, mouse=None) -> MouseController:
    monkeypatch.setattr(
        razer.mouse_controller,
        "create_device_manager",
        lambda: object(),
    )
    monkeypatch.setattr(
        razer.mouse_controller,
        "find_viper_ultimate_device",
        lambda _: mouse,
    )

    return MouseController()


def test_set_dpi_stage_returns_false_when_mouse_is_not_found(monkeypatch) -> None:
    controller = _create_controller(monkeypatch)

    assert controller.set_dpi_stage(2) is False


def test_set_dpi_stage_updates_active_stage_and_preserves_stages(
    monkeypatch,
) -> None:
    mouse = SimpleNamespace(
        dpi_stages=(
            1,
            [(800, 800), (1600, 1600), (3200, 3200)],
        ),
    )
    controller = _create_controller(monkeypatch, mouse)

    assert controller.set_dpi_stage(3) is True
    assert mouse.dpi_stages == (
        3,
        [(800, 800), (1600, 1600), (3200, 3200)],
    )


def test_set_dpi_stage_returns_false_when_setting_stage_fails(monkeypatch) -> None:
    class FailingMouse:
        def __init__(self):
            self._dpi_stages = (
                1,
                [(800, 800), (1600, 1600)],
            )

        @property
        def dpi_stages(self):
            return self._dpi_stages

        @dpi_stages.setter
        def dpi_stages(self, value):
            raise RuntimeError("DPI unavailable")

    mouse = FailingMouse()
    controller = _create_controller(monkeypatch, mouse)

    assert controller.set_dpi_stage(2) is False


def test_set_idle_time_returns_false_when_mouse_is_not_found(monkeypatch) -> None:
    controller = _create_controller(monkeypatch)

    assert controller.set_idle_time(10) is False


def test_set_idle_time_converts_minutes_to_seconds(monkeypatch) -> None:
    calls = []

    mouse = SimpleNamespace(
        set_idle_time=lambda seconds: calls.append(seconds),
    )
    controller = _create_controller(monkeypatch, mouse)

    assert controller.set_idle_time(15) is True
    assert calls == [900]


def test_set_idle_time_returns_false_when_setting_idle_time_fails(
    monkeypatch,
) -> None:
    def set_idle_time(seconds):
        raise RuntimeError("Idle time unavailable")

    mouse = SimpleNamespace(set_idle_time=set_idle_time)
    controller = _create_controller(monkeypatch, mouse)

    assert controller.set_idle_time(15) is False


def test_set_low_battery_threshold_returns_false_when_mouse_is_not_found(
    monkeypatch,
) -> None:
    controller = _create_controller(monkeypatch)

    assert controller.set_low_battery_threshold(20) is False


def test_set_low_battery_threshold_passes_threshold_unchanged(
    monkeypatch,
) -> None:
    calls = []

    mouse = SimpleNamespace(
        set_low_battery_threshold=lambda threshold: calls.append(threshold),
    )
    controller = _create_controller(monkeypatch, mouse)

    assert controller.set_low_battery_threshold(20) is True
    assert calls == [20]


def test_set_low_battery_threshold_returns_false_when_setting_threshold_fails(
    monkeypatch,
) -> None:
    def set_low_battery_threshold(threshold):
        raise RuntimeError("Threshold unavailable")

    mouse = SimpleNamespace(
        set_low_battery_threshold=set_low_battery_threshold,
    )
    controller = _create_controller(monkeypatch, mouse)

    assert controller.set_low_battery_threshold(20) is False
