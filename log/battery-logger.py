import csv
import time
from datetime import datetime
from pathlib import Path

import openrazer.client


LOG_DIR = Path(__file__).parent
INTERVAL = 1


def find_viper(device_manager):
    return next(
        (
            device
            for device in device_manager.devices
            if device.name.startswith(
                "Razer Viper Ultimate"
            )
        ),
        None,
    )


def get_log_file(viper) -> Path:
    if "(Wired)" in viper._name:
        filename = (
            "battery_wired_charge_log.csv"
        )
    else:
        filename = (
            "battery_wireless_charge_log.csv"
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

        writer.writerow(
            [
                "timestamp",
                "battery_percent",
                "is_charging",
            ]
        )


def main() -> None:
    device_manager = (
        openrazer.client.DeviceManager()
    )

    viper = find_viper(
        device_manager
    )

    if viper is None:
        print(
            "Souris non détectée.",
            flush=True,
        )
        return

    log_file = get_log_file(
        viper
    )

    initialize_log_file(
        log_file
    )

    print(
        f"Mode détecté : "
        f"{viper._name}",
        flush=True,
    )

    print(
        f"Fichier : "
        f"{log_file.name}",
        flush=True,
    )

    print(
        f"Logging toutes les "
        f"{INTERVAL} secondes.",
        flush=True,
    )

    while True:
        try:
            battery = (
                viper
                ._dbus_interfaces["power"]
                .getBattery()
            )

            is_charging = (
                viper.is_charging
            )

            timestamp = (
                datetime.now()
                .astimezone()
                .isoformat(
                    timespec="seconds"
                )
            )

            with log_file.open(
                "a",
                newline="",
                encoding="utf-8",
            ) as file:
                writer = csv.writer(
                    file
                )

                writer.writerow(
                    [
                        timestamp,
                        battery,
                        is_charging,
                    ]
                )

        except Exception as error:
            print(
                "Impossible de lire "
                f"la souris : {error}",
                flush=True,
            )

        time.sleep(
            INTERVAL
        )


if __name__ == "__main__":
    main()