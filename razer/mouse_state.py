from dataclasses import dataclass
from enum import Enum

from razer.device import (
    create_device_manager,
    find_viper_ultimate_device,
    get_charging_source,
)


class ChargingSource(Enum):
    WIRED = "wired"
    WIRELESS = "wireless"


@dataclass(slots=True)
class MouseState:
    connected: bool

    device_name: str | None

    battery: float | None
    charging: bool | None
    charging_source: ChargingSource | None

    dpi: int | None

    active_stage: int | None
    stages: list[int]

    idle_minutes: int | None
    low_battery_threshold: int | None


def _convert_dpi_stages(stages: list[tuple[int, int]]) -> list[int]:
    return [dpi_x for dpi_x, _ in stages]


def _get_disconnected_state() -> MouseState:
    return MouseState(
        connected=False,
        device_name=None,
        battery=None,
        charging=None,
        charging_source=None,
        dpi=None,
        active_stage=None,
        stages=[],
        idle_minutes=None,
        low_battery_threshold=None,
    )


def get_mouse_state() -> MouseState:
    try:
        device_manager = create_device_manager()

        mouse = find_viper_ultimate_device(device_manager)

    except Exception:  # noqa: BLE001
        return _get_disconnected_state()

    if mouse is None:
        return _get_disconnected_state()

    try:
        battery = mouse._dbus_interfaces["power"].getBattery()
        charging = mouse.is_charging

        if battery == -1.0:
            battery = None
        elif battery == 0.0:
            battery = 0 if charging else None

        dpi_x, _ = mouse.dpi

        active_stage, stages = mouse.dpi_stages

        idle_minutes = mouse.get_idle_time() // 60

        low_battery_threshold = mouse.get_low_battery_threshold()

    except Exception:  # noqa: BLE001
        return _get_disconnected_state()

    return MouseState(
        connected=True,
        device_name=mouse.name,
        battery=battery,
        charging=charging,
        charging_source=ChargingSource(get_charging_source(mouse)),
        dpi=dpi_x,
        active_stage=active_stage,
        stages=_convert_dpi_stages(stages),
        idle_minutes=idle_minutes,
        low_battery_threshold=low_battery_threshold,
    )
