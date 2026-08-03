import json

from config.paths import (
    ICON_DIR,
    MENU_ICON_DIR,
    MENU_BATTERY_ICON_DIR,
    TRAY_ICON_DIR,
    MODEL_FILE,
)

from ui.menu import create_menu
from ui.dpi_menu import create_dpi_stage_menu
from ui.status_view import StatusView
from ui.tray_view import create_indicator

from razer.mouse_state import get_mouse_state
from razer.mouse_controller import MouseController
from razer.mouse_poller import MousePoller

import gi

gi.require_version(
    "Gtk",
    "3.0",
)

from gi.repository import Gtk


class Application:
    def __init__(self):
        self.indicator = None

        self.mouse_controller = None
        self.status_view = None
        self.poller = None

    def _create_status_view(
        self,
        widgets,
        charge_models,
        icon_dir,
        tray_icon_dir,
        menu_battery_icon_dir,
    ):
        return StatusView(
            indicator=self.indicator,
            icon_dir=icon_dir,
            tray_icon_dir=tray_icon_dir,
            menu_battery_icon_dir=menu_battery_icon_dir,
            charge_models=charge_models,
            name_item=widgets.name_item,
            battery_item=widgets.battery_item,
            dpi_item=widgets.dpi_item,
            stage_item=widgets.stage_item,
            idle_item=widgets.idle_item,
            low_battery_item=widgets.low_battery_item,
            stage_items=widgets.stage_items,
        )
    
    def run(self):
        icon_dir = ICON_DIR

        menu_icon_dir = MENU_ICON_DIR

        menu_battery_icon_dir = MENU_BATTERY_ICON_DIR

        tray_icon_dir = TRAY_ICON_DIR

        with MODEL_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            charge_models = json.load(file)["sources"]

        state = get_mouse_state()

        if not state.connected:
            print(
                "Razer Viper Ultimate not detected.",
                flush=True,
            )
            return 1

        self.indicator = create_indicator(
            icon_dir,
        )

        widgets = create_menu(
            menu_icon_dir,
            menu_battery_icon_dir,
            state.device_name,
        )

        self.mouse_controller = MouseController()

        menu = widgets.menu

        stage_menu = widgets.stage_menu
        stage_items = widgets.stage_items

        self.status_view = self._create_status_view(
            widgets,
            charge_models,
            icon_dir,
            tray_icon_dir,
            menu_battery_icon_dir,
        )

        def set_active_stage(stage_number: int) -> None:
            if not self.mouse_controller.set_dpi_stage(
                stage_number,
            ):
                print(
                    "Failed to change the DPI stage.",
                    flush=True,
                )

        def handle_disconnection() -> None:
            self.status_view.show_disconnected()

        def handle_connected(state):
            self.status_view.show_connected(state)

        stage_items.extend(
            create_dpi_stage_menu(
                stage_menu,
                state.stages,
                set_active_stage,
            )
        )

        self.poller = MousePoller(
            on_connected=handle_connected,
            on_disconnected=handle_disconnection,
        )

        self.poller.poll()
        self.poller.start()

        self.indicator.set_menu(
            menu,
        )

        menu.show_all()

        return Gtk.main()