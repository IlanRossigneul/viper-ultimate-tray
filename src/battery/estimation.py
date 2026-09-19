from typing import Any


def _format_duration(
    remaining_seconds: int,
) -> str:
    if remaining_seconds < 3600:
        minutes = round(remaining_seconds / 60)

        return f"{minutes} min environ avant pleine recharge"

    hours, remainder = divmod(remaining_seconds, 3600)

    minutes = round(remainder / 60)

    if minutes == 60:
        hours += 1
        minutes = 0

    if minutes == 0:
        return f"{hours} h environ avant pleine recharge"

    return f"{hours} h {minutes} min environ avant pleine recharge"


def get_charge_estimation(
    battery: float,
    charging_source: str,
    charge_models: dict[str, dict[str, Any]],
) -> str | None:
    battery_level = int(battery)

    source = charge_models.get(charging_source)

    if source is None:
        return None

    charge_model = source.get("average", {})

    remaining_seconds = 0

    current_transition = charge_model.get(str(battery_level))

    if current_transition is not None:
        remaining_seconds += current_transition / 2

    for level in range(battery_level + 1, 100):
        transition = charge_model.get(str(level))

        if transition is not None:
            remaining_seconds += transition

    if remaining_seconds == 0:
        return None

    return _format_duration(round(remaining_seconds))
