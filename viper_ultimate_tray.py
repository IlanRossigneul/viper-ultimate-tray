import json
import sys

from config.paths import (
    ICON_DIR,
    MENU_ICON_DIR,
    MENU_BATTERY_ICON_DIR,
    TRAY_ICON_DIR,
    MODEL_FILE,
)

from battery.icons import (
    get_battery_icon,
    get_tray_icon,
)

from battery.estimation import (
    get_charge_estimation,
)

from ui.menu import create_menu
from ui.dpi_menu import create_dpi_stage_menu
from ui.status_view import StatusView
from razer.mouse_state import get_mouse_state
from razer.mouse_controller import MouseController

import gi

gi.require_version(
    "Gtk",
    "3.0",
)

gi.require_version(
    "AppIndicator3",
    "0.1",
)

from gi.repository import (
    Gtk,
    GLib,
    AppIndicator3,
)


def main() -> int:
    icon_dir = ICON_DIR

    menu_icon_dir = MENU_ICON_DIR

    menu_battery_icon_dir = MENU_BATTERY_ICON_DIR

    tray_icon_dir = TRAY_ICON_DIR

    model_file = MODEL_FILE

    with model_file.open(
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

    previous_connection_state = True

    indicator = AppIndicator3.Indicator.new(
        "viper-ultimate-tray",
        str(icon_dir / "mouse.svg"),
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )

    indicator.set_status(
        AppIndicator3.IndicatorStatus.ACTIVE
    )

    widgets = create_menu(
        menu_icon_dir,
        menu_battery_icon_dir,
        state.device_name,
    )

    mouse_controller = MouseController()

    menu = widgets.menu

    name_item = widgets.name_item
    battery_item = widgets.battery_item
    dpi_item = widgets.dpi_item
    stage_item = widgets.stage_item
    idle_item = widgets.idle_item
    low_battery_item = widgets.low_battery_item

    stage_menu = widgets.stage_menu
    stage_items = widgets.stage_items

    status_view = StatusView(
        indicator=indicator,
        icon_dir=icon_dir,
        tray_icon_dir=tray_icon_dir,
        menu_battery_icon_dir=menu_battery_icon_dir,
        charge_models=charge_models,
        name_item=name_item,
        battery_item=battery_item,
        dpi_item=dpi_item,
        stage_item=stage_item,
        idle_item=idle_item,
        low_battery_item=low_battery_item,
        stage_items=stage_items,
    )

    polychromatic_action = widgets.polychromatic_action
    input_remapper_action = widgets.input_remapper_action
    quit_action = widgets.quit_action

    def set_active_stage(stage_number: int) -> None:
        if not mouse_controller.set_dpi_stage(
            stage_number
        ):
            print(
                "Failed to change the DPI stage.",
                flush=True,
            )

        update_mouse_status()

    def handle_disconnection() -> None:
        nonlocal previous_connection_state

        if previous_connection_state:
            print(
                "Mouse disconnected.",
                flush=True,
            )

        previous_connection_state = False
        status_view.show_disconnected()

    def mark_as_connected() -> None:
        nonlocal previous_connection_state

        if not previous_connection_state:
            print(
                "Mouse reconnected.",
                flush=True,
            )

        previous_connection_state = True

    def update_mouse_status() -> None:
        try:
            # Recreate the device manager intentionally to detect
            # state changes between wireless and wired modes.
            state = get_mouse_state()

        except Exception:
            handle_disconnection()
            return

        if not state.connected:
            handle_disconnection()
            return

        mark_as_connected()

        status_view.show_connected(
            state,
        )

    stage_items.extend(
        create_dpi_stage_menu(
            stage_menu,
            state.stages,
            set_active_stage,
        )
    )

    update_mouse_status()

    # Automatically refresh the mouse status
    def refresh_mouse_status():
        update_mouse_status()
        return True

    GLib.timeout_add(
        2000,
        refresh_mouse_status,
    )

    indicator.set_menu(
        menu
    )

    menu.show_all()

    return Gtk.main()


if __name__ == "__main__":
    sys.exit(main())