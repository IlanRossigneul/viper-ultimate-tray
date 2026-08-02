import openrazer.client


def create_device_manager():
    return openrazer.client.DeviceManager()


def find_viper_ultimate_device(manager):
    return next(
        (
            device
            for device in manager.devices
            if device.name.startswith("Razer Viper Ultimate")
        ),
        None,
    )


def get_charging_source(device):
    if "(Wired)" in device._name:
        return "wired"

    return "wireless"