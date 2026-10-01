import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QLockFile

from app.application import Application
from battery_logs.battery_logger import BatteryLogEntry
from razer.mouse_state import MouseState


def _connected_state() -> MouseState:
    return MouseState(
        connected=True,
        device_name="Razer Viper Ultimate",
        battery=75.0,
        charging=False,
        charging_source=None,
        dpi=800,
        active_stage=1,
        stages=[800, 1600],
        idle_minutes=5,
        low_battery_threshold=15,
    )


def _disconnected_state() -> MouseState:
    return MouseState(
        connected=False,
        device_name=None,
        battery=None,
        charging=None,
        charging_source=None,
        dpi=None,
        active_stage=None,
        stages=[],
        idle_minutes=None,
        low_battery_threshold=None,
    )


def test_parse_args_defaults_to_info() -> None:
    application = Application()

    assert application._parse_args([]) == logging.INFO


def test_parse_args_accepts_info() -> None:
    application = Application()

    assert application._parse_args(["--info"]) == logging.INFO


def test_parse_args_accepts_debug() -> None:
    application = Application()

    assert application._parse_args(["--debug"]) == logging.DEBUG


def test_parse_args_rejects_conflicting_log_levels() -> None:
    application = Application()

    with pytest.raises(SystemExit):
        application._parse_args(["--info", "--debug"])


def test_acquire_instance_lock_succeeds() -> None:
    application = Application()

    application._instance_lock = MagicMock()
    application._instance_lock.tryLock.return_value = True

    assert application._acquire_instance_lock()

    application._instance_lock.tryLock.assert_called_once_with(0)


def test_acquire_instance_lock_fails_when_another_instance_is_running(
    caplog,
) -> None:
    application = Application()

    application._instance_lock = MagicMock()
    application._instance_lock.tryLock.return_value = False

    with caplog.at_level(logging.WARNING):
        assert not application._acquire_instance_lock()

    application._instance_lock.tryLock.assert_called_once_with(0)

    assert "Another Viper Ultimate Tray instance is already running." in caplog.text


def test_instance_lock_allows_only_one_holder(tmp_path) -> None:
    lock_path = tmp_path / "viper-ultimate-tray.lock"

    first_lock = QLockFile(str(lock_path))
    second_lock = QLockFile(str(lock_path))

    first_lock.setStaleLockTime(0)
    second_lock.setStaleLockTime(0)

    assert first_lock.tryLock(0)
    assert not second_lock.tryLock(0)

    first_lock.unlock()

    assert second_lock.tryLock(0)

    second_lock.unlock()


def test_open_battery_logger_creates_and_shows_window() -> None:
    application = Application()

    with patch("app.application.BatteryLoggerWindow") as window_class:
        application._open_battery_logger()

    window = window_class.return_value

    window_class.assert_called_once_with()
    window.show.assert_called_once_with()
    window.raise_.assert_called_once_with()
    window.activateWindow.assert_called_once_with()

    assert application.battery_logger_window is window


def test_open_battery_logger_reuses_existing_window() -> None:
    application = Application()
    application.battery_logger_window = MagicMock()

    with patch("app.application.BatteryLoggerWindow") as window_class:
        application._open_battery_logger()

    window_class.assert_not_called()

    application.battery_logger_window.show.assert_called_once_with()
    application.battery_logger_window.raise_.assert_called_once_with()
    application.battery_logger_window.activateWindow.assert_called_once_with()


def test_open_battery_logger_connects_window_signals() -> None:
    application = Application()

    with patch("app.application.BatteryLoggerWindow") as window_class:
        application._open_battery_logger()

    window = window_class.return_value

    window.start_requested.connect.assert_called_once_with(
        application._start_battery_logger,
    )
    window.stop_requested.connect.assert_called_once_with(
        application._stop_battery_logger,
    )

    entry = BatteryLogEntry(
        timestamp="2026-09-19T19:00:00+02:00",
        battery_percent=31.8,
        is_charging=False,
    )

    application._handle_battery_logger_started("Razer Viper Ultimate", 1)
    application._handle_battery_log_entry(entry)
    application._handle_battery_logger_finished()

    window.display_start.assert_called_once_with(
        "Razer Viper Ultimate",
        1,
    )
    window.display_log_entry.assert_called_once_with(entry)
    window.display_stop.assert_called_once_with()


def test_open_battery_logger_does_not_reconnect_signals() -> None:
    application = Application()
    application.battery_logger_window = MagicMock()

    application._open_battery_logger()

    application.battery_logger_window.start_requested.connect.assert_not_called()
    application.battery_logger_window.stop_requested.connect.assert_not_called()

    application.battery_logger_window.display_start.assert_not_called()
    application.battery_logger_window.display_log_entry.assert_not_called()
    application.battery_logger_window.display_stop.assert_not_called()


def test_handle_battery_log_entry_forwards_entry_to_signal() -> None:
    application = Application()
    entry = BatteryLogEntry(
        timestamp="2026-09-19T19:00:00+02:00",
        battery_percent=31.8,
        is_charging=False,
    )

    received_entries: list[BatteryLogEntry] = []

    application.battery_log_entry_received.connect(received_entries.append)

    application._handle_battery_log_entry(entry)

    assert received_entries == [entry]


def test_handle_battery_logger_started_forwards_to_signal() -> None:
    application = Application()

    received_values: list[tuple[str, int]] = []

    application.battery_logger_started.connect(
        lambda mode, interval: received_values.append((mode, interval)),
    )

    application._handle_battery_logger_started(
        "Razer Viper Ultimate",
        1,
    )

    assert received_values == [
        ("Razer Viper Ultimate", 1),
    ]


def test_handle_battery_logger_finished_forwards_to_signal() -> None:
    application = Application()

    finished_calls = 0

    def on_finished() -> None:
        nonlocal finished_calls
        finished_calls += 1

    application.battery_logger_finished.connect(on_finished)

    application._handle_battery_logger_finished()

    assert finished_calls == 1


def test_start_battery_logger_does_nothing_without_log_manager() -> None:
    application = Application()

    application._start_battery_logger()


def test_start_battery_logger_starts_logger_and_updates_window() -> None:
    application = Application()
    application.log_manager = MagicMock()
    application.battery_logger_window = MagicMock()
    application.menu_widgets = MagicMock()

    application.log_manager.start_logger.return_value = True

    with patch("app.application.logger.info") as logger_info:
        application._start_battery_logger()

    application.log_manager.start_logger.assert_called_once_with()
    logger_info.assert_called_once_with("Battery logger started.")
    application.battery_logger_window.set_logging_state.assert_called_once_with(
        application.battery_logger_started_at,
    )
    application.menu_widgets.logs_item.setText.assert_called_once()


def test_start_battery_logger_does_not_update_window_when_start_fails() -> None:
    application = Application()
    application.log_manager = MagicMock()
    application.battery_logger_window = MagicMock()

    application.log_manager.start_logger.return_value = False

    with patch("app.application.logger.info") as logger_info:
        application._start_battery_logger()

    application.log_manager.start_logger.assert_called_once_with()
    logger_info.assert_not_called()
    application.battery_logger_window.set_logging_state.assert_not_called()


def test_start_battery_logger_starts_logger_without_window() -> None:
    application = Application()
    application.log_manager = MagicMock()

    application.log_manager.start_logger.return_value = True

    with patch("app.application.logger.info") as logger_info:
        application._start_battery_logger()

    application.log_manager.start_logger.assert_called_once_with()
    logger_info.assert_called_once_with("Battery logger started.")


def test_stop_battery_logger_does_nothing_without_log_manager() -> None:
    application = Application()

    application._stop_battery_logger()


def test_stop_battery_logger_stops_logger_and_updates_window() -> None:
    application = Application()
    application.log_manager = MagicMock()
    application.battery_logger_window = MagicMock()
    application.menu_widgets = MagicMock()

    application.log_manager.stop_logger.return_value = True

    with patch("app.application.logger.info") as logger_info:
        application._stop_battery_logger()

    application.log_manager.stop_logger.assert_called_once_with()
    logger_info.assert_called_once_with("Battery logger stopped.")
    application.battery_logger_window.set_idle_state.assert_called_once_with(
        None,
    )
    application.menu_widgets.logs_item.setText.assert_called_once_with(
        "Journalisation",
    )


def test_stop_battery_logger_does_not_update_window_when_stop_fails() -> None:
    application = Application()
    application.log_manager = MagicMock()
    application.battery_logger_window = MagicMock()

    application.log_manager.stop_logger.return_value = False

    with patch("app.application.logger.info") as logger_info:
        application._stop_battery_logger()

    application.log_manager.stop_logger.assert_called_once_with()
    logger_info.assert_not_called()
    application.battery_logger_window.set_idle_state.assert_not_called()


def test_stop_battery_logger_stops_logger_without_window() -> None:
    application = Application()
    application.log_manager = MagicMock()

    application.log_manager.stop_logger.return_value = True

    with patch("app.application.logger.info") as logger_info:
        application._stop_battery_logger()

    application.log_manager.stop_logger.assert_called_once_with()
    logger_info.assert_called_once_with("Battery logger stopped.")


def test_set_active_stage_logs_error_when_controller_fails() -> None:
    application = Application()
    application.mouse_controller = MagicMock()
    application.mouse_controller.set_dpi_stage.return_value = False

    with patch("app.application.logger.error") as logger_error:
        application._set_active_stage(2)

    application.mouse_controller.set_dpi_stage.assert_called_once_with(2)
    logger_error.assert_called_once_with("Failed to change the DPI stage.")


def test_set_idle_time_logs_error_when_controller_fails() -> None:
    application = Application()
    application.mouse_controller = MagicMock()
    application.mouse_controller.set_idle_time.return_value = False

    with patch("app.application.logger.error") as logger_error:
        application._set_idle_time(10)

    application.mouse_controller.set_idle_time.assert_called_once_with(10)
    logger_error.assert_called_once_with("Failed to change the hibernation time.")


def test_set_low_battery_threshold_logs_error_when_controller_fails() -> None:
    application = Application()
    application.mouse_controller = MagicMock()
    application.mouse_controller.set_low_battery_threshold.return_value = False

    with patch("app.application.logger.error") as logger_error:
        application._set_low_battery_threshold(15)

    application.mouse_controller.set_low_battery_threshold.assert_called_once_with(15)
    logger_error.assert_called_once_with(
        "Failed to change the low battery threshold.",
    )


def test_handle_disconnection_resets_notifications() -> None:
    application = Application()
    application.status_view = MagicMock()
    application.notification_manager = MagicMock()

    application._handle_disconnection()

    application.status_view.show_disconnected.assert_called_once_with()
    application.notification_manager.reset.assert_called_once_with()


def test_handle_disconnection_works_without_notification_manager() -> None:
    application = Application()
    application.status_view = MagicMock()

    application._handle_disconnection()

    application.status_view.show_disconnected.assert_called_once_with()


def test_handle_connected_updates_status_and_notifications() -> None:
    application = Application()
    application.status_view = MagicMock()
    application.notification_manager = MagicMock()
    state = _connected_state()

    application._handle_connected(state)

    application.status_view.show_connected.assert_called_once_with(state)
    application.notification_manager.update.assert_called_once_with(state)


def test_handle_connected_works_without_notification_manager() -> None:
    application = Application()
    application.status_view = MagicMock()
    state = _connected_state()

    application._handle_connected(state)

    application.status_view.show_connected.assert_called_once_with(state)


def test_create_status_view_passes_menu_and_charge_model_dependencies() -> None:
    application = Application()
    application.indicator = MagicMock()
    application.menu_icon_dir = Path("/menu")
    application.tray_icon_dir = Path("/tray")
    application.menu_battery_icon_dir = Path("/battery")

    widgets = MagicMock()
    charge_models = {"wired": {}, "wireless": {}}

    with patch("app.application.StatusView") as status_view:
        result = application._create_status_view(widgets, charge_models)

    status_view.assert_called_once_with(
        indicator=application.indicator,
        menu_icon_dir=application.menu_icon_dir,
        tray_icon_dir=application.tray_icon_dir,
        menu_battery_icon_dir=application.menu_battery_icon_dir,
        charge_models=charge_models,
        name_item=widgets.name_item,
        battery_item=widgets.battery_item,
        dpi_item=widgets.dpi_item,
        stage_item=widgets.stage_item,
        idle_item=widgets.idle_item,
        idle_items=widgets.idle_items,
        low_battery_item=widgets.low_battery_item,
        low_battery_items=widgets.low_battery_items,
        stage_items=widgets.stage_items,
    )
    assert result is status_view.return_value


def test_run_returns_error_when_mouse_is_not_connected() -> None:
    application = Application()
    disconnected_state = _disconnected_state()

    with (
        patch.object(application, "_parse_args", return_value=logging.INFO),
        patch("app.application.setup_logger") as setup_logger,
        patch(
            "app.application.QApplication.instance",
            return_value=MagicMock(),
        ),
        patch("app.application.load_charge_models", return_value={}),
        patch(
            "app.application.get_mouse_state",
            return_value=disconnected_state,
        ),
        patch("app.application.logger.error") as logger_error,
        patch("app.application.create_indicator") as create_indicator,
    ):
        result = application.run([])

    assert result == 1
    setup_logger.assert_called_once_with(logging.INFO)
    logger_error.assert_called_once_with("Razer Viper Ultimate not detected.")
    create_indicator.assert_not_called()


def test_run_orchestrates_application_startup() -> None:
    application = Application()

    app = MagicMock()
    indicator = MagicMock()
    widgets = MagicMock()
    widgets.stage_items = []
    widgets.idle_items = []
    widgets.low_battery_items = []

    state = _connected_state()
    charge_models = {"wired": {}, "wireless": {}}

    with (
        patch.object(application, "_parse_args", return_value=logging.DEBUG),
        patch.object(
            application,
            "_acquire_instance_lock",
            return_value=True,
        ) as acquire_instance_lock,
        patch("app.application.setup_logger") as setup_logger,
        patch("app.application.QApplication.instance", return_value=app),
        patch(
            "app.application.load_charge_models",
            return_value=charge_models,
        ),
        patch("app.application.get_mouse_state", return_value=state),
        patch(
            "app.application.create_indicator",
            return_value=indicator,
        ) as create_indicator,
        patch("app.application.LogManager") as log_manager,
        patch(
            "app.application.MouseNotificationManager",
        ) as notification_manager,
        patch(
            "app.application.create_menu",
            return_value=widgets,
        ) as create_menu,
        patch("app.application.MouseController") as mouse_controller,
        patch.object(
            application,
            "_create_status_view",
        ) as create_status_view,
        patch(
            "app.application.create_dpi_stage_menu",
            return_value=["dpi-item"],
        ) as create_dpi_menu,
        patch(
            "app.application.create_idle_time_menu",
            return_value=["idle-item"],
        ) as create_idle_menu,
        patch(
            "app.application.create_low_battery_menu",
            return_value=["battery-item"],
        ) as create_low_battery_menu,
        patch("app.application.MousePoller") as mouse_poller,
    ):
        app.exec.return_value = 42
        create_status_view.return_value = MagicMock()

        result = application.run([])

    assert result == 42

    acquire_instance_lock.assert_called_once_with()

    setup_logger.assert_called_once_with(logging.DEBUG)
    app.setQuitOnLastWindowClosed.assert_called_once_with(False)

    create_indicator.assert_called_once_with(application.icon_dir)

    log_manager.assert_called_once_with(
        application.battery_logs_dir,
        on_started=application._handle_battery_logger_started,
        on_entry=application._handle_battery_log_entry,
        on_finished=application._handle_battery_logger_finished,
        on_session_changed=application._handle_battery_logger_session_changed,
        on_samples=application._handle_charge_samples,
        on_model=application._handle_charge_model,
    )

    notification_manager.assert_called_once_with()

    create_menu.assert_called_once_with(
        application.menu_icon_dir,
        application.menu_battery_icon_dir,
        application.menu_log_icon_dir,
        state.device_name,
    )

    widgets.battery_logger_action.triggered.connect.assert_called_once_with(
        application._open_battery_logger,
    )

    mouse_controller.assert_called_once_with()
    create_status_view.assert_called_once_with(widgets, charge_models)

    create_dpi_menu.assert_called_once_with(
        widgets.stage_menu,
        state.stages,
        application.menu_icon_dir,
        application._set_active_stage,
    )

    create_idle_menu.assert_called_once_with(
        widgets.idle_menu,
        application.menu_icon_dir / "hibernation.svg",
        application._set_idle_time,
    )

    create_low_battery_menu.assert_called_once_with(
        widgets.low_battery_menu,
        application.menu_icon_dir / "low_battery.svg",
        application._set_low_battery_threshold,
    )

    mouse_poller.assert_called_once_with(
        on_connected=application._handle_connected,
        on_disconnected=application._handle_disconnection,
    )

    mouse_poller.return_value.start.assert_called_once_with()
    mouse_poller.return_value.stop.assert_called_once_with()

    indicator.setContextMenu.assert_called_once_with(widgets.menu)
    app.exec.assert_called_once_with()

    assert widgets.stage_items == ["dpi-item"]
    assert widgets.idle_items == ["idle-item"]
    assert widgets.low_battery_items == ["battery-item"]


def test_shutdown_stops_running_logger() -> None:
    application = Application()
    application.log_manager = MagicMock()
    application.log_manager.is_logger_running.return_value = True

    application._shutdown()

    application.log_manager.is_logger_running.assert_called_once_with()
    application.log_manager.stop_logger.assert_called_once_with()


def test_shutdown_does_nothing_when_logger_is_not_running() -> None:
    application = Application()
    application.log_manager = MagicMock()
    application.log_manager.is_logger_running.return_value = False

    application._shutdown()

    application.log_manager.is_logger_running.assert_called_once_with()
    application.log_manager.stop_logger.assert_not_called()


def test_shutdown_does_nothing_without_log_manager() -> None:
    application = Application()

    application._shutdown()


def test_handle_charge_samples_forwards_samples_to_signal() -> None:
    application = Application()
    samples = {"wired": [], "wireless": []}

    received_samples: list[dict] = []

    application.charge_samples_received.connect(received_samples.append)

    application._handle_charge_samples(samples)

    assert received_samples == [samples]


def test_handle_charge_model_forwards_model_to_signal() -> None:
    application = Application()
    model = {
        "wired": {
            "statistics": {"sample_count": 0, "last_updated": None},
            "average": {},
        },
        "wireless": {
            "statistics": {"sample_count": 0, "last_updated": None},
            "average": {},
        },
    }

    received_models: list[dict] = []

    application.charge_model_received.connect(received_models.append)

    application._handle_charge_model(model)

    assert received_models == [model]


def test_open_charge_data_creates_and_initializes_window() -> None:
    application = Application()
    application.log_manager = MagicMock()

    samples = {"wired": [], "wireless": []}
    model = {
        "wired": {
            "statistics": {"sample_count": 1, "last_updated": "2026-09-19"},
            "average": {"0": 120},
        },
        "wireless": {
            "statistics": {"sample_count": 2, "last_updated": "2026-09-20"},
            "average": {"0": 125},
        },
    }

    application.log_manager.load_charge_samples.return_value = samples
    application.log_manager.load_charge_model.return_value = model

    with patch("app.application.ChargeDataWindow") as window_class:
        application._open_charge_data()

    window = window_class.return_value

    window_class.assert_called_once_with(
        on_update_sample=application._update_charge_sample,
        on_delete_sample=application._delete_charge_sample,
    )

    application.log_manager.load_charge_samples.assert_called_once_with()
    application.log_manager.load_charge_model.assert_called_once_with()

    window.set_samples.assert_called_once_with(samples)
    window.set_model.assert_called_once_with(model)

    window.show.assert_called_once_with()
    window.raise_.assert_called_once_with()
    window.activateWindow.assert_called_once_with()

    assert application.charge_data_window is window


def test_open_charge_data_connects_window_signals() -> None:
    application = Application()

    with patch("app.application.ChargeDataWindow") as window_class:
        application._open_charge_data()

    window = window_class.return_value

    samples = {"wired": [], "wireless": []}
    model = {
        "wired": {
            "statistics": {"sample_count": 0, "last_updated": None},
            "average": {},
        },
        "wireless": {
            "statistics": {"sample_count": 0, "last_updated": None},
            "average": {},
        },
    }

    application.charge_samples_received.emit(samples)
    application.charge_model_received.emit(model)

    window.set_samples.assert_called_once_with(samples)
    window.set_model.assert_called_once_with(model)


def test_open_charge_data_reuses_existing_window_and_refreshes_data() -> None:
    application = Application()
    application.charge_data_window = MagicMock()
    application.log_manager = MagicMock()

    samples = {"wired": [], "wireless": []}
    model = {
        "wired": {
            "statistics": {"sample_count": 1, "last_updated": None},
            "average": {"0": 120},
        },
        "wireless": {
            "statistics": {"sample_count": 0, "last_updated": None},
            "average": {},
        },
    }

    application.log_manager.load_charge_samples.return_value = samples
    application.log_manager.load_charge_model.return_value = model

    with patch("app.application.ChargeDataWindow") as window_class:
        application._open_charge_data()

    window_class.assert_not_called()

    application.log_manager.load_charge_samples.assert_called_once_with()
    application.log_manager.load_charge_model.assert_called_once_with()

    application.charge_data_window.set_samples.assert_called_once_with(samples)
    application.charge_data_window.set_model.assert_called_once_with(model)

    application.charge_data_window.show.assert_called_once_with()
    application.charge_data_window.raise_.assert_called_once_with()
    application.charge_data_window.activateWindow.assert_called_once_with()


def test_start_battery_logger_records_start_time() -> None:
    application = Application()
    application.log_manager = MagicMock()
    application.log_manager.start_logger.return_value = True

    start_time = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

    with patch("app.application.datetime") as datetime_mock:
        datetime_mock.now.return_value = start_time

        application._start_battery_logger()

    assert application.battery_logger_started_at == start_time
    assert application.battery_logger_last_duration is None


def test_start_battery_logger_does_not_update_timer_when_start_fails() -> None:
    application = Application()
    application.log_manager = MagicMock()
    application.log_manager.start_logger.return_value = False

    previous_start = datetime(
        2026,
        9,
        28,
        11,
        0,
        tzinfo=timezone.utc,
    )
    previous_duration = timedelta(minutes=12)

    application.battery_logger_started_at = previous_start
    application.battery_logger_last_duration = previous_duration

    application._start_battery_logger()

    assert application.battery_logger_started_at == previous_start
    assert application.battery_logger_last_duration == previous_duration


def test_stop_battery_logger_records_last_duration() -> None:
    application = Application()
    application.log_manager = MagicMock()
    application.log_manager.stop_logger.return_value = True

    start_time = datetime(
        2026,
        9,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )
    stop_time = datetime(
        2026,
        9,
        28,
        12,
        17,
        32,
        tzinfo=timezone.utc,
    )

    application.battery_logger_started_at = start_time

    with patch("app.application.datetime") as datetime_mock:
        datetime_mock.now.return_value = stop_time

        application._stop_battery_logger()

    assert application.battery_logger_started_at is None
    assert application.battery_logger_last_duration == timedelta(
        minutes=17,
        seconds=32,
    )


def test_stop_battery_logger_clears_start_time_without_previous_timestamp() -> None:
    application = Application()
    application.log_manager = MagicMock()
    application.log_manager.stop_logger.return_value = True

    application._stop_battery_logger()

    assert application.battery_logger_started_at is None
    assert application.battery_logger_last_duration is None


def test_update_battery_logger_menu_shows_idle_label() -> None:
    application = Application()
    application.menu_widgets = MagicMock()

    application._update_battery_logger_menu()

    application.menu_widgets.logs_item.setText.assert_called_once_with(
        "Journalisation",
    )


def test_update_battery_logger_menu_shows_elapsed_time() -> None:
    application = Application()
    application.menu_widgets = MagicMock()

    start_time = datetime(
        2026,
        9,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )
    current_time = datetime(
        2026,
        9,
        28,
        12,
        17,
        32,
        tzinfo=timezone.utc,
    )

    application.battery_logger_started_at = start_time

    with patch("app.application.datetime") as datetime_mock:
        datetime_mock.now.return_value = current_time

        application._update_battery_logger_menu()

    application.menu_widgets.logs_item.setText.assert_called_once_with(
        "Journalisation : 00:17:32",
    )


def test_handle_connected_updates_battery_logger_menu() -> None:
    application = Application()
    application.status_view = MagicMock()
    application.menu_widgets = MagicMock()

    state = _connected_state()

    with patch.object(
        application,
        "_update_battery_logger_menu",
    ) as update_menu:
        application._handle_connected(state)

    update_menu.assert_called_once_with()


def test_handle_battery_logger_session_changed_notifies_connection_change() -> None:
    application = Application()
    application.notification_manager = MagicMock()

    application._handle_battery_logger_session_changed(
        "Razer Viper Ultimate (Wireless)",
        "Razer Viper Ultimate (Wired)",
    )

    application.notification_manager.notify_connection_change.assert_called_once_with(
        "Razer Viper Ultimate (Wireless)",
        "Razer Viper Ultimate (Wired)",
    )


def test_handle_battery_logger_session_changed_works_without_notification_manager() -> (
    None
):
    application = Application()

    application._handle_battery_logger_session_changed(
        "Razer Viper Ultimate (Wireless)",
        "Razer Viper Ultimate (Wired)",
    )
