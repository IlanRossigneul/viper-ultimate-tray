from types import SimpleNamespace

from razer.device import find_viper_ultimate_device, get_charging_source


def test_find_viper_ultimate_device_returns_first_matching_device() -> None:
    other_mouse = SimpleNamespace(name="Razer DeathAdder V3")
    first_viper = SimpleNamespace(name="Razer Viper Ultimate")
    second_viper = SimpleNamespace(name="Razer Viper Ultimate (Wired)")

    manager = SimpleNamespace(
        devices=[other_mouse, first_viper, second_viper],
    )

    assert find_viper_ultimate_device(manager) is first_viper


def test_find_viper_ultimate_device_returns_none_when_no_viper_is_present() -> None:
    manager = SimpleNamespace(
        devices=[
            SimpleNamespace(name="Razer DeathAdder V3"),
            SimpleNamespace(name="Razer Basilisk V3"),
        ],
    )

    assert find_viper_ultimate_device(manager) is None


def test_get_charging_source_returns_wired_for_wired_device() -> None:
    device = SimpleNamespace(name="Razer Viper Ultimate (Wired)")

    assert get_charging_source(device) == "wired"


def test_get_charging_source_returns_wireless_for_wireless_device() -> None:
    device = SimpleNamespace(name="Razer Viper Ultimate")

    assert get_charging_source(device) == "wireless"
