def get_battery_icon(
    battery: float,
    is_charging: bool,
) -> str:
    if battery <= 10:
        level = 0
    elif battery <= 25:
        level = 1
    elif battery <= 50:
        level = 2
    elif battery <= 75:
        level = 3
    else:
        level = 4

    prefix = "battery-charging" if is_charging else "battery"

    return f"{prefix}-{level}.svg"


def get_tray_icon(
    battery: float,
    is_charging: bool,
) -> str:
    battery_level = int(battery)

    suffix = "_c" if is_charging else ""

    return f"bat_{battery_level}{suffix}.png"
