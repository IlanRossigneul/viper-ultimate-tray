import pytest

from battery.icons import get_battery_icon, get_tray_icon


@pytest.mark.parametrize(
    ("battery", "expected_level"),
    [
        (0, 0),
        (10, 0),
        (11, 1),
        (25, 1),
        (26, 2),
        (50, 2),
        (51, 3),
        (75, 3),
        (76, 4),
        (100, 4),
    ],
)
def test_get_battery_icon_selects_expected_level(
    battery: float,
    expected_level: int,
) -> None:
    assert get_battery_icon(battery, False) == f"battery-{expected_level}.svg"


def test_get_battery_icon_uses_charging_prefix() -> None:
    assert get_battery_icon(50, True) == "battery-charging-2.svg"


@pytest.mark.parametrize(
    ("battery", "charging", "expected"),
    [
        (42.9, False, "bat_42.png"),
        (42.9, True, "bat_42_c.png"),
        (0, False, "bat_0.png"),
        (100, True, "bat_100_c.png"),
    ],
)
def test_get_tray_icon_uses_integer_battery_and_charging_suffix(
    battery: float,
    charging: bool,
    expected: str,
) -> None:
    assert get_tray_icon(battery, charging) == expected
