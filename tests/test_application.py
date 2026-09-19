import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.application import Application
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


def test_update_logger_menu_state_disables_start_and_enables_stop_when_running() -> (
    None
):
    application = Application()
    application.log_manager = MagicMock()
    application.menu_widgets = MagicMock()

    application.log_manager.is_logger_running.return_value = True

    application._update_logger_menu_state()

    application.menu_widgets.battery_logger_start_action.setEnabled.assert_called_once_with(
        False,
    )
    application.menu_widgets.battery_logger_stop_action.setEnabled.assert_called_once_with(
        True,
    )


def test_update_logger_menu_state_enables_start_and_disables_stop_when_stopped() -> (
    None
):
    application = Application()
    application.log_manager = MagicMock()
    application.menu_widgets = MagicMock()

    application.log_manager.is_logger_running.return_value = False

    application._update_logger_menu_state()

    application.menu_widgets.battery_logger_start_action.setEnabled.assert_called_once_with(
        True,
    )
    application.menu_widgets.battery_logger_stop_action.setEnabled.assert_called_once_with(
        False,
    )


def test_update_logger_menu_state_does_nothing_without_log_manager() -> None:
    application = Application()
    application.menu_widgets = MagicMock()

    application._update_logger_menu_state()

    application.menu_widgets.battery_logger_start_action.setEnabled.assert_not_called()
    application.menu_widgets.battery_logger_stop_action.setEnabled.assert_not_called()


def test_start_battery_logger_starts_and_updates_menu_state() -> None:
    application = Application()
    application.log_manager = MagicMock()

    application.log_manager.start_logger.return_value = True

    with (
        patch("app.application.logger.info") as logger_info,
        patch.object(
            application,
            "_update_logger_menu_state",
        ) as update_menu,
    ):
        application._start_battery_logger()

    application.log_manager.start_logger.assert_called_once_with()
    logger_info.assert_called_once_with("Battery logger started.")
    update_menu.assert_called_once_with()


def test_start_battery_logger_does_not_log_when_start_fails() -> None:
    application = Application()
    application.log_manager = MagicMock()

    application.log_manager.start_logger.return_value = False

    with (
        patch("app.application.logger.info") as logger_info,
        patch.object(
            application,
            "_update_logger_menu_state",
        ) as update_menu,
    ):
        application._start_battery_logger()

    logger_info.assert_not_called()
    update_menu.assert_called_once_with()


def test_stop_battery_logger_stops_and_updates_menu_state() -> None:
    application = Application()
    application.log_manager = MagicMock()

    application.log_manager.stop_logger.return_value = True

    with (
        patch("app.application.logger.info") as logger_info,
        patch.object(
            application,
            "_update_logger_menu_state",
        ) as update_menu,
    ):
        application._stop_battery_logger()

    application.log_manager.stop_logger.assert_called_once_with()
    logger_info.assert_called_once_with("Battery logger stopped.")
    update_menu.assert_called_once_with()


def test_stop_battery_logger_does_not_log_when_stop_fails() -> None:
    application = Application()
    application.log_manager = MagicMock()

    application.log_manager.stop_logger.return_value = False

    with (
        patch("app.application.logger.info") as logger_info,
        patch.object(
            application,
            "_update_logger_menu_state",
        ) as update_menu,
    ):
        application._stop_battery_logger()

    logger_info.assert_not_called()
    update_menu.assert_called_once_with()


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


def test_handle_disconnection_updates_status_and_resets_notifications() -> None:
    application = Application()
    application.status_view = MagicMock()
    application.notification_manager = MagicMock()

    application._handle_disconnection()

    application.status_view.show_disconnected.assert_called_once_with()
    application.notification_manager.reset.assert_called_once_with()


def test_handle_connected_updates_status_and_notifications() -> None:
    application = Application()
    application.status_view = MagicMock()
    application.notification_manager = MagicMock()
    state = _connected_state()

    application._handle_connected(state)

    application.status_view.show_connected.assert_called_once_with(state)
    application.notification_manager.update.assert_called_once_with(state)


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
        patch("app.application.QApplication.instance", return_value=MagicMock()),
        patch("app.application.load_charge_models", return_value={}),
        patch("app.application.get_mouse_state", return_value=disconnected_state),
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
        patch("app.application.setup_logger") as setup_logger,
        patch("app.application.QApplication.instance", return_value=app),
        patch("app.application.load_charge_models", return_value=charge_models),
        patch("app.application.get_mouse_state", return_value=state),
        patch(
            "app.application.create_indicator", return_value=indicator
        ) as create_indicator,
        patch("app.application.LogManager") as log_manager,
        patch(
            "app.application.MouseNotificationManager",
        ) as notification_manager,
        patch("app.application.create_menu", return_value=widgets) as create_menu,
        patch("app.application.MouseController") as mouse_controller,
        patch.object(application, "_create_status_view") as create_status_view,
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

    setup_logger.assert_called_once_with(logging.DEBUG)
    app.setQuitOnLastWindowClosed.assert_called_once_with(False)

    create_indicator.assert_called_once_with(application.icon_dir)
    log_manager.assert_called_once_with(application.battery_logs_dir)
    notification_manager.assert_called_once_with()

    create_menu.assert_called_once_with(
        application.menu_icon_dir,
        application.menu_battery_icon_dir,
        application.menu_log_icon_dir,
        state.device_name,
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

    mouse_poller.return_value.poll.assert_called_once_with()
    mouse_poller.return_value.start.assert_called_once_with()

    indicator.setContextMenu.assert_called_once_with(widgets.menu)
    app.exec.assert_called_once_with()

    assert widgets.stage_items == ["dpi-item"]
    assert widgets.idle_items == ["idle-item"]
    assert widgets.low_battery_items == ["battery-item"]
