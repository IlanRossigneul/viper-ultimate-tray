import argparse
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from KStatusNotifierItem import KStatusNotifierItem
from PySide6.QtCore import QLockFile, QObject, Signal, Slot
from PySide6.QtWidgets import QApplication

from battery.models import load_charge_models
from battery_logs.battery_logger import BatteryLogEntry
from battery_logs.manager import LogManager
from config.paths import (
    BATTERY_LOGS_DIR,
    ICON_DIR,
    INSTANCE_LOCK_FILE,
    MENU_BATTERY_ICON_DIR,
    MENU_ICON_DIR,
    MENU_LOG_ICON_DIR,
    TRAY_ICON_DIR,
)
from notifications.mouse_notifications import MouseNotificationManager
from razer.mouse_controller import MouseController
from razer.mouse_poller import MousePoller
from razer.mouse_state import MouseState, get_mouse_state
from ui.battery_logger_window import BatteryLoggerWindow
from ui.charge_data_window import ChargeDataWindow
from ui.dpi_menu import create_dpi_stage_menu
from ui.idle_menu import create_idle_time_menu
from ui.low_battery_menu import create_low_battery_menu
from ui.menu import MenuWidgets, create_menu
from ui.status_view import StatusView
from ui.tray_view import create_indicator

from .logging import setup_logger

logger = logging.getLogger(__name__)


class Application(QObject):
    battery_logger_started = Signal(str, int)
    battery_logger_start_failed = Signal(str)
    battery_log_entry_received = Signal(BatteryLogEntry)
    battery_logger_finished = Signal()
    battery_logger_session_changed = Signal(str, str)
    charge_samples_received = Signal(object)
    charge_model_received = Signal(object)

    _battery_logger_started = Signal(str, int)
    _battery_logger_start_failed = Signal(str)
    _battery_log_entry = Signal(BatteryLogEntry)
    _battery_logger_finished = Signal()
    _battery_logger_session_changed = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.indicator: KStatusNotifierItem | None = None

        self.mouse_controller: MouseController | None = None
        self.status_view: StatusView | None = None
        self.poller: MousePoller | None = None
        self.log_manager: LogManager | None = None
        self.menu_widgets: MenuWidgets | None = None
        self.battery_logger_window: BatteryLoggerWindow | None = None
        self.charge_data_window: ChargeDataWindow | None = None
        self.battery_logger_started_at: datetime | None = None
        self.battery_logger_last_duration: timedelta | None = None
        self.notification_manager: MouseNotificationManager | None = None

        self._battery_logger_started.connect(
            self._handle_battery_logger_started,
        )
        self._battery_logger_start_failed.connect(
            self._handle_battery_logger_start_failed,
        )
        self._battery_log_entry.connect(
            self._handle_battery_log_entry,
        )
        self._battery_logger_finished.connect(
            self._handle_battery_logger_finished,
        )
        self._battery_logger_session_changed.connect(
            self._handle_battery_logger_session_changed,
        )

        self.icon_dir = ICON_DIR
        self.battery_logs_dir = BATTERY_LOGS_DIR
        self.menu_icon_dir = MENU_ICON_DIR
        self.menu_battery_icon_dir = MENU_BATTERY_ICON_DIR
        self.menu_log_icon_dir = MENU_LOG_ICON_DIR
        self.tray_icon_dir = TRAY_ICON_DIR

        self._instance_lock = QLockFile(str(INSTANCE_LOCK_FILE))
        self._instance_lock.setStaleLockTime(0)

    def _parse_args(
        self,
        args: list[str],
    ) -> int:
        """Parse command-line arguments."""
        parser = argparse.ArgumentParser()

        group = parser.add_mutually_exclusive_group()

        group.add_argument(
            "--info",
            dest="log_level",
            action="store_const",
            const=logging.INFO,
        )

        group.add_argument(
            "--debug",
            dest="log_level",
            action="store_const",
            const=logging.DEBUG,
        )

        parsed = parser.parse_args(args)

        return parsed.log_level if parsed.log_level is not None else logging.INFO

    def _acquire_instance_lock(self) -> bool:
        """Acquire the application instance lock."""

        if self._instance_lock.tryLock(0):
            return True

        logger.warning(
            "Another Viper Ultimate Tray instance is already running.",
        )
        return False

    def _create_status_view(
        self,
        widgets: MenuWidgets,
        charge_models: dict[str, dict[str, Any]],
    ) -> StatusView:
        return StatusView(
            indicator=self.indicator,
            menu_icon_dir=self.menu_icon_dir,
            tray_icon_dir=self.tray_icon_dir,
            menu_battery_icon_dir=self.menu_battery_icon_dir,
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

    def _open_battery_logger(self) -> None:
        if self.battery_logger_window is None:
            self.battery_logger_window = BatteryLoggerWindow()

            self.battery_logger_window.start_requested.connect(
                self._start_battery_logger,
            )

            self.battery_logger_window.stop_requested.connect(
                self._stop_battery_logger,
            )

            self.battery_logger_started.connect(
                self.battery_logger_window.display_start,
            )

            self.battery_logger_start_failed.connect(
                self.battery_logger_window.display_start_failed,
            )

            self.battery_log_entry_received.connect(
                self.battery_logger_window.display_log_entry,
            )

            self.battery_logger_finished.connect(
                self.battery_logger_window.display_stop,
            )

            self.battery_logger_session_changed.connect(
                self.battery_logger_window.display_session_change,
            )

            if self.battery_logger_started_at is not None:
                self.battery_logger_window.set_logging_state(
                    self.battery_logger_started_at,
                )
            else:
                self.battery_logger_window.set_idle_state(
                    self.battery_logger_last_duration,
                )

        self.battery_logger_window.show()
        self.battery_logger_window.raise_()
        self.battery_logger_window.activateWindow()

    def _open_charge_data(self) -> None:
        if self.charge_data_window is None:
            self.charge_data_window = ChargeDataWindow(
                on_update_sample=self._update_charge_sample,
                on_delete_sample=self._delete_charge_sample,
            )

            self.charge_samples_received.connect(
                self.charge_data_window.set_samples,
            )

            self.charge_model_received.connect(
                self.charge_data_window.set_model,
            )

        if self.log_manager is not None:
            self.charge_data_window.set_samples(
                self.log_manager.load_charge_samples(),
            )
            self.charge_data_window.set_model(
                self.log_manager.load_charge_model(),
            )

        self.charge_data_window.show()
        self.charge_data_window.raise_()
        self.charge_data_window.activateWindow()

    @Slot(BatteryLogEntry)
    def _handle_battery_log_entry(self, entry: BatteryLogEntry) -> None:
        self.battery_log_entry_received.emit(entry)

    @Slot(str, int)
    def _handle_battery_logger_started(
        self,
        mode: str,
        interval_seconds: int,
    ) -> None:
        self.battery_logger_started_at = datetime.now(timezone.utc)
        self.battery_logger_last_duration = None

        logger.info("Battery logger started.")

        self._update_battery_logger_menu()

        if self.battery_logger_window is not None:
            self.battery_logger_window.set_logging_state(
                self.battery_logger_started_at,
            )

        self.battery_logger_started.emit(mode, interval_seconds)

    @Slot(str)
    def _handle_battery_logger_start_failed(
        self,
        reason: str,
    ) -> None:
        logger.error(
            "Battery logger failed to start: %s",
            reason,
        )

        self.battery_logger_started_at = None

        if self.battery_logger_window is not None:
            self.battery_logger_window.set_idle_state(
                self.battery_logger_last_duration,
            )

        self.battery_logger_start_failed.emit(reason)

    @Slot()
    def _handle_battery_logger_finished(self) -> None:
        stop_time = datetime.now(timezone.utc)

        if self.battery_logger_started_at is not None:
            self.battery_logger_last_duration = (
                stop_time - self.battery_logger_started_at
            )

        self.battery_logger_started_at = None

        logger.info("Battery logger stopped.")

        self._update_battery_logger_menu()

        if self.battery_logger_window is not None:
            self.battery_logger_window.set_idle_state(
                self.battery_logger_last_duration,
            )

        self.battery_logger_finished.emit()

    @Slot(str, str)
    def _handle_battery_logger_session_changed(
        self,
        old_mode: str,
        new_mode: str,
    ) -> None:
        self.battery_logger_session_changed.emit(old_mode, new_mode)

        if self.notification_manager is not None:
            self.notification_manager.notify_connection_change(
                old_mode,
                new_mode,
            )

    def _update_battery_logger_menu(self) -> None:
        if self.menu_widgets is None:
            return

        if self.battery_logger_started_at is None:
            self.menu_widgets.logs_item.setText("Journalisation")
            return

        elapsed = datetime.now(timezone.utc) - self.battery_logger_started_at
        total_seconds = int(elapsed.total_seconds())

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.menu_widgets.logs_item.setText(
            f"Journalisation : {hours:02}:{minutes:02}:{seconds:02}"
        )

    def _start_battery_logger(self) -> None:
        if self.log_manager is None:
            return

        self.log_manager.start_logger()

    def _stop_battery_logger(self) -> None:
        if self.log_manager is None:
            return

        self.log_manager.stop_logger()

    def _handle_charge_samples(self, samples: dict[str, Any]) -> None:
        self.charge_samples_received.emit(samples)

    def _handle_charge_model(self, model: dict[str, Any]) -> None:
        self.charge_model_received.emit(model)

    def _update_charge_sample(
        self,
        mode: str,
        created_at: str,
        transitions: dict[str, int],
    ) -> None:
        if self.log_manager is not None:
            self.log_manager.update_charge_sample(
                mode,
                created_at,
                transitions,
            )

    def _delete_charge_sample(
        self,
        mode: str,
        created_at: str,
    ) -> None:
        if self.log_manager is not None:
            self.log_manager.delete_charge_sample(
                mode,
                created_at,
            )

    def _set_active_stage(self, stage_number: int) -> None:
        if not self.mouse_controller.set_dpi_stage(stage_number):
            logger.error("Failed to change the DPI stage.")

    def _set_idle_time(self, minutes: int) -> None:
        if not self.mouse_controller.set_idle_time(minutes):
            logger.error("Failed to change the hibernation time.")

    def _set_low_battery_threshold(self, threshold: int) -> None:
        if not self.mouse_controller.set_low_battery_threshold(threshold):
            logger.error("Failed to change the low battery threshold.")

    def _handle_disconnection(self) -> None:
        self.status_view.show_disconnected()

        if self.notification_manager is not None:
            self.notification_manager.reset()

    def _handle_connected(self, state: MouseState) -> None:
        self.status_view.show_connected(state)

        if self.notification_manager is not None:
            self.notification_manager.update(state)

        self._update_battery_logger_menu()

    def _shutdown(self) -> None:
        if self.log_manager is not None and self.log_manager.is_logger_running():
            self.log_manager.stop_logger()

    def run(self, args: list[str]) -> int:
        log_level = self._parse_args(args)
        setup_logger(log_level)

        if not self._acquire_instance_lock():
            return 0

        app = QApplication.instance()

        if app is None:
            app = QApplication([])

        app.setDesktopFileName("viper-ultimate-tray")
        app.setQuitOnLastWindowClosed(False)

        app.aboutToQuit.connect(self._shutdown)

        charge_models = load_charge_models()

        state = get_mouse_state()

        if not state.connected:
            logger.error("Razer Viper Ultimate not detected.")
            return 1

        self.indicator = create_indicator(self.icon_dir)

        self.log_manager = LogManager(
            self.battery_logs_dir,
            on_started=self._battery_logger_started.emit,
            on_start_failed=self._battery_logger_start_failed.emit,
            on_entry=self._battery_log_entry.emit,
            on_finished=self._battery_logger_finished.emit,
            on_session_changed=self._battery_logger_session_changed.emit,
            on_samples=self._handle_charge_samples,
            on_model=self._handle_charge_model,
        )

        self.notification_manager = MouseNotificationManager()

        self.menu_widgets = create_menu(
            self.menu_icon_dir,
            self.menu_battery_icon_dir,
            self.menu_log_icon_dir,
            state.device_name,
        )

        self.menu_widgets.battery_logger_action.triggered.connect(
            self._open_battery_logger,
        )

        self.menu_widgets.charge_data_action.triggered.connect(
            self._open_charge_data,
        )

        self.mouse_controller = MouseController()

        stage_menu = self.menu_widgets.stage_menu
        stage_items = self.menu_widgets.stage_items

        idle_menu = self.menu_widgets.idle_menu
        idle_items = self.menu_widgets.idle_items

        low_battery_menu = self.menu_widgets.low_battery_menu
        low_battery_items = self.menu_widgets.low_battery_items

        self.status_view = self._create_status_view(self.menu_widgets, charge_models)

        stage_items.extend(
            create_dpi_stage_menu(
                stage_menu,
                state.stages,
                self.menu_icon_dir,
                self._set_active_stage,
            )
        )

        idle_items.extend(
            create_idle_time_menu(
                idle_menu,
                self.menu_icon_dir / "hibernation.svg",
                self._set_idle_time,
            )
        )

        low_battery_items.extend(
            create_low_battery_menu(
                low_battery_menu,
                self.menu_icon_dir / "low_battery.svg",
                self._set_low_battery_threshold,
            )
        )

        self.poller = MousePoller(
            on_connected=self._handle_connected,
            on_disconnected=self._handle_disconnection,
        )

        self.poller.start()

        self.indicator.setContextMenu(self.menu_widgets.menu)

        try:
            return app.exec()
        finally:
            if self.poller is not None:
                self.poller.stop()

            self._instance_lock.unlock()
