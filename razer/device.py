from openrazer.client import DeviceManager
from openrazer.client.devices.mice import RazerMouse


def create_device_manager() -> DeviceManager:
    return DeviceManager()


def find_viper_ultimate_device(manager: DeviceManager) -> RazerMouse | None:
    return next(
        (
            device
            for device in manager.devices
            if device.name.startswith("Razer Viper Ultimate")
        ),
        None,
    )


def get_charging_source(device: RazerMouse) -> str:
    if "(Wired)" in device.name:
        return "wired"

    return "wireless"
