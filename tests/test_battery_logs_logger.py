import csv
from unittest.mock import MagicMock, patch

from battery_logs.battery_logger import BatteryLogger


def test_get_log_file_uses_wired_filename(tmp_path):
    logger = BatteryLogger(tmp_path)

    mouse = MagicMock()
    mouse.name = "Razer Viper Ultimate (Wired)"

    assert logger._get_log_file(mouse) == (tmp_path / "battery_wired_charge_log.csv")


def test_get_log_file_uses_wireless_filename(tmp_path):
    logger = BatteryLogger(tmp_path)

    mouse = MagicMock()
    mouse.name = "Razer Viper Ultimate"

    assert logger._get_log_file(mouse) == (tmp_path / "battery_wireless_charge_log.csv")


def test_initialize_log_file_writes_header(tmp_path):
    logger = BatteryLogger(tmp_path)
    log_file = tmp_path / "battery_wireless_charge_log.csv"

    logger._initialize_log_file(log_file)

    with log_file.open(newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))

    assert rows == [
        ["timestamp", "battery_percent", "is_charging"],
    ]


def test_stop_sets_running_to_false(tmp_path):
    logger = BatteryLogger(tmp_path)

    logger.stop()

    assert logger.running is False


def test_run_reports_start_failure_when_mouse_is_not_detected(tmp_path):
    on_started = MagicMock()
    on_start_failed = MagicMock()

    logger = BatteryLogger(
        tmp_path,
        on_started=on_started,
        on_start_failed=on_start_failed,
    )

    with (
        patch(
            "battery_logs.battery_logger.create_device_manager",
            return_value=MagicMock(),
        ),
        patch(
            "battery_logs.battery_logger.find_viper_ultimate_device",
            return_value=None,
        ),
        patch("battery_logs.battery_logger.logger.error") as error,
    ):
        logger.run()

    assert list(tmp_path.iterdir()) == []

    error.assert_called_once_with("Mouse not detected.")
    on_start_failed.assert_called_once_with("mouse_not_detected")
    on_started.assert_not_called()


def test_run_creates_log_with_raw_battery_value(tmp_path):
    logger = BatteryLogger(tmp_path, interval_seconds=1)

    mouse = MagicMock()
    mouse.name = "Razer Viper Ultimate"
    mouse._dbus_interfaces["power"].getBattery.return_value = 31.8
    mouse.is_charging = False

    def stop_after_sleep(_interval):
        logger.stop()

    with (
        patch(
            "battery_logs.battery_logger.create_device_manager",
            return_value=MagicMock(),
        ),
        patch(
            "battery_logs.battery_logger.find_viper_ultimate_device",
            return_value=mouse,
        ),
        patch(
            "battery_logs.battery_logger.time.sleep",
            side_effect=stop_after_sleep,
        ),
        patch("battery_logs.battery_logger.datetime") as datetime_mock,
    ):
        datetime_mock.now.return_value.astimezone.return_value.isoformat.return_value = "2026-09-19T19:00:00+02:00"

        logger.run()

    log_file = tmp_path / "battery_wireless_charge_log.csv"

    with log_file.open(newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))

    assert rows == [
        ["timestamp", "battery_percent", "is_charging"],
        ["2026-09-19T19:00:00+02:00", "31.8", "False"],
        ["2026-09-19T19:00:00+02:00", "31.8", "False"],
    ]


def test_run_logs_charging_state(tmp_path):
    logger = BatteryLogger(tmp_path, interval_seconds=1)

    mouse = MagicMock()
    mouse.name = "Razer Viper Ultimate (Wired)"
    mouse._dbus_interfaces["power"].getBattery.return_value = 98.0392156862745
    mouse.is_charging = True

    def stop_after_sleep(_interval):
        logger.stop()

    with (
        patch(
            "battery_logs.battery_logger.create_device_manager",
            return_value=MagicMock(),
        ),
        patch(
            "battery_logs.battery_logger.find_viper_ultimate_device",
            return_value=mouse,
        ),
        patch(
            "battery_logs.battery_logger.time.sleep",
            side_effect=stop_after_sleep,
        ),
        patch("battery_logs.battery_logger.datetime") as datetime_mock,
    ):
        datetime_mock.now.return_value.astimezone.return_value.isoformat.return_value = "2026-09-19T19:01:00+02:00"

        logger.run()

    log_file = tmp_path / "battery_wired_charge_log.csv"

    with log_file.open(newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))

    assert rows == [
        ["timestamp", "battery_percent", "is_charging"],
        [
            "2026-09-19T19:01:00+02:00",
            "98.0392156862745",
            "True",
        ],
        [
            "2026-09-19T19:01:00+02:00",
            "98.0392156862745",
            "True",
        ],
    ]


def test_run_logs_exception_and_continues(tmp_path):
    logger = BatteryLogger(tmp_path, interval_seconds=1)

    mouse = MagicMock()
    mouse.name = "Razer Viper Ultimate"
    mouse._dbus_interfaces["power"].getBattery.side_effect = [
        RuntimeError("DBus failure"),
        42.5,
    ]
    mouse.is_charging = False

    sleep_calls = 0

    def sleep_and_stop(_interval):
        nonlocal sleep_calls
        sleep_calls += 1

        if sleep_calls == 2:
            logger.stop()

    with (
        patch(
            "battery_logs.battery_logger.create_device_manager",
            return_value=MagicMock(),
        ),
        patch(
            "battery_logs.battery_logger.find_viper_ultimate_device",
            return_value=mouse,
        ),
        patch(
            "battery_logs.battery_logger.time.sleep",
            side_effect=sleep_and_stop,
        ),
        patch("battery_logs.battery_logger.datetime") as datetime_mock,
        patch("battery_logs.battery_logger.logger.exception") as exception,
    ):
        datetime_mock.now.return_value.astimezone.return_value.isoformat.return_value = "2026-09-19T19:02:00+02:00"

        logger.run()

    log_file = tmp_path / "battery_wireless_charge_log.csv"

    with log_file.open(newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))

    assert rows == [
        ["timestamp", "battery_percent", "is_charging"],
        ["2026-09-19T19:02:00+02:00", "42.5", "False"],
        ["2026-09-19T19:02:00+02:00", "42.5", "False"],
    ]

    exception.assert_called_once_with("Failed to log battery data.")


def test_run_rotates_log_when_connection_mode_changes(tmp_path):
    logger = BatteryLogger(tmp_path, interval_seconds=1)

    wireless_mouse = MagicMock()
    wireless_mouse.name = "Razer Viper Ultimate"
    wireless_mouse._dbus_interfaces["power"].getBattery.return_value = 80.0
    wireless_mouse.is_charging = False

    wired_mouse = MagicMock()
    wired_mouse.name = "Razer Viper Ultimate (Wired)"
    wired_mouse._dbus_interfaces["power"].getBattery.return_value = 81.0
    wired_mouse.is_charging = False

    session_changes: list[tuple[str, str]] = []

    def on_session_changed(old_mode: str, new_mode: str) -> None:
        session_changes.append((old_mode, new_mode))

    find_calls = 0

    def find_mouse(_device_manager):
        nonlocal find_calls
        find_calls += 1

        if find_calls == 1:
            return wireless_mouse
        if find_calls == 2:
            return wireless_mouse
        if find_calls in (3, 4):
            return None
        if find_calls == 5:
            return wired_mouse

        logger.stop()
        return wired_mouse

    logger.on_session_changed = on_session_changed

    with (
        patch(
            "battery_logs.battery_logger.create_device_manager",
            return_value=MagicMock(),
        ),
        patch(
            "battery_logs.battery_logger.find_viper_ultimate_device",
            side_effect=find_mouse,
        ),
        patch(
            "battery_logs.battery_logger.time.sleep",
        ),
        patch("battery_logs.battery_logger.datetime") as datetime_mock,
    ):
        datetime_mock.now.return_value.astimezone.return_value.isoformat.side_effect = [
            "2026-01-01T12:00:00+01:00",
            "2026-01-01T12:00:04+01:00",
        ]

        logger.run()

    assert session_changes == [
        (
            "Razer Viper Ultimate",
            "Razer Viper Ultimate (Wired)",
        )
    ]

    wireless_log = tmp_path / "battery_wireless_charge_log.csv"
    wired_log = tmp_path / "battery_wired_charge_log.csv"

    with wireless_log.open(encoding="utf-8", newline="") as file:
        wireless_rows = list(csv.reader(file))

    with wired_log.open(encoding="utf-8", newline="") as file:
        wired_rows = list(csv.reader(file))

    assert wireless_rows == [
        ["timestamp", "battery_percent", "is_charging"],
        ["2026-01-01T12:00:00+01:00", "80.0", "False"],
        ["2026-01-01T12:00:00+01:00", "80.0", "False"],
    ]

    assert wired_rows == [
        ["timestamp", "battery_percent", "is_charging"],
        ["2026-01-01T12:00:04+01:00", "81.0", "False"],
        ["2026-01-01T12:00:04+01:00", "81.0", "False"],
    ]

    wireless_mouse._dbus_interfaces["power"].getBattery.assert_called_once()
    wired_mouse._dbus_interfaces["power"].getBattery.assert_called_once()


def test_run_keeps_session_when_connection_mode_is_unchanged(tmp_path):
    logger = BatteryLogger(tmp_path, interval_seconds=1)

    first_mouse = MagicMock()
    first_mouse.name = "Razer Viper Ultimate"
    first_mouse._dbus_interfaces["power"].getBattery.return_value = 80.0
    first_mouse.is_charging = False

    second_mouse = MagicMock()
    second_mouse.name = "Razer Viper Ultimate"
    second_mouse._dbus_interfaces["power"].getBattery.return_value = 81.0
    second_mouse.is_charging = False

    session_changes: list[tuple[str, str]] = []
    sleep_calls = 0

    def on_session_changed(old_mode: str, new_mode: str) -> None:
        session_changes.append((old_mode, new_mode))

    def find_mouse(_device_manager):
        if sleep_calls == 0:
            return first_mouse
        if sleep_calls == 1:
            return None
        return second_mouse

    def sleep_and_stop(_interval: int) -> None:
        nonlocal sleep_calls
        sleep_calls += 1

        if sleep_calls == 3:
            logger.stop()

    logger.on_session_changed = on_session_changed

    with (
        patch(
            "battery_logs.battery_logger.create_device_manager",
            return_value=MagicMock(),
        ),
        patch(
            "battery_logs.battery_logger.find_viper_ultimate_device",
            side_effect=find_mouse,
        ),
        patch(
            "battery_logs.battery_logger.time.sleep",
            side_effect=sleep_and_stop,
        ),
        patch("battery_logs.battery_logger.datetime") as datetime_mock,
    ):
        datetime_mock.now.return_value.astimezone.return_value.isoformat.side_effect = [
            "2026-01-01T12:00:00+01:00",
            "2026-01-01T12:00:04+01:00",
        ]

        logger.run()

    assert session_changes == []

    log_file = tmp_path / "battery_wireless_charge_log.csv"

    with log_file.open(encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))

    assert rows == [
        ["timestamp", "battery_percent", "is_charging"],
        ["2026-01-01T12:00:00+01:00", "80.0", "False"],
        ["2026-01-01T12:00:00+01:00", "80.0", "False"],
        ["2026-01-01T12:00:04+01:00", "81.0", "False"],
        ["2026-01-01T12:00:04+01:00", "81.0", "False"],
    ]

    first_mouse._dbus_interfaces["power"].getBattery.assert_called_once()
    second_mouse._dbus_interfaces["power"].getBattery.assert_called_once()
