import csv
import time
from datetime import datetime
from pathlib import Path

from openrazer.client import DeviceManager


LOG_DIR = Path(__file__).resolve().parent
LOG_INTERVAL_SECONDS = 1


def find_viper(device_manager: DeviceManager) -> object | None:
    return next(
        (
            device
            for device in device_manager.devices
            if device.name.startswith("Razer Viper Ultimate")
        ),
        None,
    )


def get_log_file(mouse) -> Path:
    filename = (
        "battery_wired_charge_log.csv"
        if "(Wired)" in mouse._name
        else "battery_wireless_charge_log.csv"
    )

    return LOG_DIR / filename


def initialize_log_file(
    log_file: Path,
) -> None:
    with log_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "battery_percent", "is_charging"])


def main() -> None:
    device_manager = DeviceManager()

    mouse = find_viper(device_manager)

    if mouse is None:
        print("Mouse not detected.", flush=True)
        return

    log_file = get_log_file(mouse)

    initialize_log_file(log_file)

    print(f"Detected mode: {mouse._name}", flush=True)

    print(f"Log file: {log_file.name}", flush=True)

    print(f"Logging every {LOG_INTERVAL_SECONDS} second(s).", flush=True)

    while True:
        try:
            battery = mouse._dbus_interfaces["power"].getBattery()

            is_charging = mouse.is_charging

            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

            with log_file.open(
                "a",
                newline="",
                encoding="utf-8",
            ) as file:
                writer = csv.writer(file)

                writer.writerow(
                    [
                        timestamp,
                        battery,
                        is_charging,
                    ]
                )

        except Exception as error:
            print(f"Unable to read mouse state: {error}", flush=True)

        time.sleep(LOG_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()