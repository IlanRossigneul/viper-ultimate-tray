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


def test_request_stop_stops_running_logger(tmp_path):
    logger = BatteryLogger(tmp_path)

    with patch("battery_logs.battery_logger.logger.info") as info:
        logger._request_stop(2, None)

    assert logger.running is False
    info.assert_called_once_with("Stopping battery logger...")


def test_request_stop_does_nothing_when_already_stopped(tmp_path):
    logger = BatteryLogger(tmp_path)
    logger.stop()

    with patch("battery_logs.battery_logger.logger.info") as info:
        logger._request_stop(2, None)

    info.assert_not_called()


def test_run_does_nothing_when_mouse_is_not_detected(tmp_path):
    logger = BatteryLogger(tmp_path)

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
