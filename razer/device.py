from typing import Any

from openrazer.client import DeviceManager


def create_device_manager() -> DeviceManager:
    return DeviceManager()


def find_viper_ultimate_device(
    manager: DeviceManager,
) -> Any | None:
    return next(
        (
            device
            for device in manager.devices
            if device.name.startswith("Razer Viper Ultimate")
        ),
        None,
    )


def get_charging_source(
    device: Any,
) -> str:
    if "(Wired)" in device._name:
        return "wired"

    return "wireless"