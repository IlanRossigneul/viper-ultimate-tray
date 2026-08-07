from typing import Any

import gi

from battery.models import load_charge_models

from config.paths import (
    ICON_DIR,
    LOG_DIR,
    MENU_BATTERY_ICON_DIR,
    MENU_LOG_ICON_DIR,
    MENU_ICON_DIR,
    TRAY_ICON_DIR,
)

from log.manager import LogManager

from razer.mouse_controller import MouseController
from razer.mouse_poller import MousePoller
from razer.mouse_state import MouseState, get_mouse_state

from ui.dpi_menu import create_dpi_stage_menu
from ui.menu import MenuWidgets, create_menu
from ui.status_view import StatusView
from ui.tray_view import create_indicator

gi.require_version("Gtk", "3.0")

from gi.repository import AppIndicator3, Gtk


class Application:
    def __init__(self) -> None:
        self.indicator: AppIndicator3.Indicator | None = None

        self.mouse_controller: MouseController | None = None
        self.status_view: StatusView | None = None
        self.poller: MousePoller | None = None
        self.log_manager: LogManager | None = None
        self.menu_widgets: MenuWidgets | None = None

        self.icon_dir = ICON_DIR
        self.log_dir = LOG_DIR
        self.menu_icon_dir = MENU_ICON_DIR
        self.menu_battery_icon_dir = MENU_BATTERY_ICON_DIR
        self.menu_log_icon_dir = MENU_LOG_ICON_DIR
        self.tray_icon_dir = TRAY_ICON_DIR

    def _create_status_view(
        self,
        widgets: MenuWidgets,
        charge_models: dict[str, dict[str, Any]],
    ) -> StatusView:
        return StatusView(
            indicator=self.indicator,
            icon_dir=self.icon_dir,
            tray_icon_dir=self.tray_icon_dir,
            menu_battery_icon_dir=self.menu_battery_icon_dir,
            charge_models=charge_models,
            name_item=widgets.name_item,
            battery_item=widgets.battery_item,
            dpi_item=widgets.dpi_item,
            stage_item=widgets.stage_item,
            idle_item=widgets.idle_item,
            low_battery_item=widgets.low_battery_item,
            stage_items=widgets.stage_items,
        )


    def _update_logger_menu_state(self) -> None:
        if self.log_manager is None or self.menu_widgets is None:
            return

        running = self.log_manager.is_logger_running()

        self.menu_widgets.battery_logger_start_action.set_sensitive(not running)
        self.menu_widgets.battery_logger_stop_action.set_sensitive(running)


    def _start_battery_logger(self) -> None:
        if self.log_manager is None:
            return

        if self.log_manager.start_logger():
            print("Battery logger started.", flush=True)

        self._update_logger_menu_state()


    def _stop_battery_logger(self) -> None:
        if self.log_manager is None:
            return

        if self.log_manager.stop_logger():
            print("Battery logger stopped.", flush=True)

        self._update_logger_menu_state()


    def _set_active_stage(self, stage_number: int) -> None:
        if not self.mouse_controller.set_dpi_stage(stage_number):
            print("Failed to change the DPI stage.", flush=True)


    def _handle_disconnection(self) -> None:
        self.status_view.show_disconnected()


    def _handle_connected(
        self,
        state: MouseState,
    ) -> None:
        self.status_view.show_connected(state)


    def run(self) -> int:
        charge_models = load_charge_models()

        state = get_mouse_state()

        if not state.connected:
            print("Razer Viper Ultimate not detected.", flush=True)
            return 1

        self.indicator = create_indicator(self.icon_dir)

        self.log_manager = LogManager(self.log_dir)

        self.menu_widgets = create_menu(
            self.menu_icon_dir,
            self.menu_battery_icon_dir,
            self.menu_log_icon_dir,
            state.device_name,
        )

        self.menu_widgets.battery_logger_start_action.connect(
            "activate",
            lambda *_: self._start_battery_logger(),
        )

        self.menu_widgets.battery_logger_stop_action.connect(
            "activate",
            lambda *_: self._stop_battery_logger(),
        )

        self._update_logger_menu_state()

        self.mouse_controller = MouseController()

        menu = self.menu_widgets.menu

        stage_menu = self.menu_widgets.stage_menu
        stage_items = self.menu_widgets.stage_items

        self.status_view = self._create_status_view(self.menu_widgets, charge_models)

        stage_items.extend(
            create_dpi_stage_menu(
                stage_menu,
                state.stages,
                self._set_active_stage,
            )
        )

        self.poller = MousePoller(
            on_connected=self._handle_connected,
            on_disconnected=self._handle_disconnection,
        )

        self.poller.poll()
        self.poller.start()

        self.indicator.set_menu(menu)

        menu.show_all()

        return Gtk.main()