from unittest.mock import MagicMock

from notifications import mouse_notifications
from notifications.mouse_notifications import MouseNotificationManager
from razer.mouse_state import ChargingSource, MouseState


def _create_state(
    *,
    connected: bool = True,
    battery: float | None = 50.0,
    charging: bool | None = False,
) -> MouseState:
    return MouseState(
        connected=connected,
        device_name="Razer Viper Ultimate",
        battery=battery,
        charging=charging,
        charging_source=(ChargingSource.WIRELESS if connected else None),
        dpi=1600 if connected else None,
        active_stage=1 if connected else None,
        stages=[800, 1600, 3200] if connected else [],
        idle_minutes=5 if connected else None,
        low_battery_threshold=15 if connected else None,
    )


def _create_manager(monkeypatch) -> MouseNotificationManager:
    monkeypatch.setattr(
        mouse_notifications.Notify,
        "init",
        lambda _: True,
    )

    return MouseNotificationManager()


def _capture_notifications(manager: MouseNotificationManager) -> list[tuple]:
    notifications = []

    def notify(state, message, icon_path, sound_name):
        notifications.append(
            (state, message, icon_path, sound_name),
        )

    manager._notify = notify

    return notifications


def test_first_update_does_not_notify(monkeypatch) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=50))

    assert notifications == []


def test_low_battery_notification_is_sent_when_crossing_30_percent(
    monkeypatch,
) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=31.8))
    manager.update(_create_state(battery=30.8))

    assert len(notifications) == 1
    assert notifications[0][1] == "Batterie faible — 30 %"
    assert notifications[0][2] == mouse_notifications.LOW_BATTERY_ICON_PATH
    assert notifications[0][3] == "dialog-warning"


def test_very_low_battery_notification_is_sent_when_crossing_15_percent(
    monkeypatch,
) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=16.8))
    manager.update(_create_state(battery=15.8))

    assert len(notifications) == 1
    assert notifications[0][1] == "Batterie faible — 15 %"
    assert notifications[0][2] == mouse_notifications.VERY_LOW_BATTERY_ICON_PATH
    assert notifications[0][3] == "battery-low"


def test_extremely_low_battery_notification_is_sent_when_crossing_5_percent(
    monkeypatch,
) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=6.8))
    manager.update(_create_state(battery=5.8))

    assert len(notifications) == 1
    assert notifications[0][1] == "Batterie faible — 5 %"
    assert notifications[0][2] == (mouse_notifications.EXTREMELY_LOW_BATTERY_ICON_PATH)
    assert notifications[0][3] == "battery-caution"


def test_low_battery_notification_is_not_repeated_while_remaining_below_threshold(
    monkeypatch,
) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=31.8))
    manager.update(_create_state(battery=30.8))
    manager.update(_create_state(battery=29.8))
    manager.update(_create_state(battery=20.8))

    assert len(notifications) == 1
    assert notifications[0][1] == "Batterie faible — 30 %"


def test_low_battery_notification_is_rearmed_after_battery_rises_above_threshold(
    monkeypatch,
) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=31.8))
    manager.update(_create_state(battery=30.8))
    manager.update(_create_state(battery=32.8))
    manager.update(_create_state(battery=30.8))

    assert len(notifications) == 2
    assert all(
        notification[1] == "Batterie faible — 30 %" for notification in notifications
    )


def test_low_battery_notifications_are_not_sent_while_charging(
    monkeypatch,
) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=31, charging=True))
    manager.update(_create_state(battery=30, charging=True))

    assert notifications == []


def test_crossing_multiple_low_battery_thresholds_sends_each_notification(
    monkeypatch,
) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=31.8))
    manager.update(_create_state(battery=5.8))

    assert [notification[1] for notification in notifications] == [
        "Batterie faible — 30 %",
        "Batterie faible — 15 %",
        "Batterie faible — 5 %",
    ]


def test_charge_complete_notification_is_sent_when_reaching_100_percent(
    monkeypatch,
) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=99, charging=True))
    manager.update(_create_state(battery=100, charging=True))

    assert len(notifications) == 1
    assert notifications[0][1] == ("Charge terminée — batterie à 100 %")
    assert notifications[0][2] == mouse_notifications.FULL_BATTERY_ICON_PATH
    assert notifications[0][3] == "battery-full"


def test_charge_complete_notification_is_not_repeated_at_100_percent(
    monkeypatch,
) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=99, charging=True))
    manager.update(_create_state(battery=100, charging=True))
    manager.update(_create_state(battery=100, charging=True))

    assert len(notifications) == 1


def test_charge_complete_notification_is_rearmed_after_charging_stops(
    monkeypatch,
) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=99, charging=True))
    manager.update(_create_state(battery=100, charging=True))
    manager.update(_create_state(battery=100, charging=False))
    manager.update(_create_state(battery=99, charging=True))
    manager.update(_create_state(battery=100, charging=True))

    assert len(notifications) == 2
    assert all(
        notification[1] == "Charge terminée — batterie à 100 %"
        for notification in notifications
    )


def test_no_notification_is_sent_when_battery_is_unknown(monkeypatch) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=None, charging=False))
    manager.update(_create_state(battery=None, charging=True))

    assert notifications == []


def test_disconnected_state_does_not_send_notifications(monkeypatch) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=31))
    manager.update(
        _create_state(
            connected=False,
            battery=None,
            charging=None,
        ),
    )

    assert notifications == []


def test_reset_clears_previous_state_and_notification_flags(
    monkeypatch,
) -> None:
    manager = _create_manager(monkeypatch)
    notifications = _capture_notifications(manager)

    manager.update(_create_state(battery=31.8))
    manager.update(_create_state(battery=30.8))

    manager.reset()

    manager.update(_create_state(battery=32.8))
    manager.update(_create_state(battery=30.8))

    assert len(notifications) == 2


def test_connection_change_notification_is_sent(monkeypatch) -> None:
    manager = _create_manager(monkeypatch)
    notification = MagicMock()

    monkeypatch.setattr(
        mouse_notifications.Notify.Notification,
        "new",
        MagicMock(return_value=notification),
    )

    manager.notify_connection_change(
        "Razer Viper Ultimate (Wireless)",
        "Razer Viper Ultimate (Wired)",
    )

    mouse_notifications.Notify.Notification.new.assert_called_once_with(
        "🖱️ Razer Viper Ultimate",
        (
            "Changement de connexion : "
            "Razer Viper Ultimate (Wireless) → "
            "Razer Viper Ultimate (Wired)"
        ),
        None,
    )

    notification.set_timeout.assert_called_once_with(10000)
    notification.show.assert_called_once_with()
    notification.set_hint.assert_called_once()
