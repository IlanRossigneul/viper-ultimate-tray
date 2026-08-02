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

    def set_disconnected_state() -> None:
        indicator.set_icon_full(
            str(icon_dir / "mouse.svg"),
            "Razer Viper Ultimate",
        )

        name_item.label_widget.set_text(
            "Razer Viper Ultimate déconnectée"
        )

        battery_item.label_widget.set_text(
            "Batterie : —"
        )

        dpi_item.label_widget.set_text(
            "DPI : —"
        )

        stage_item.label_widget.set_text(
            "Plage active : —"
        )

        idle_item.label_widget.set_text(
            "Hibernation : —"
        )

        low_battery_item.label_widget.set_text(
            "Basse consommation : —"
        )

        battery_item.set_sensitive(
            False
        )

        dpi_item.set_sensitive(
            False
        )

        stage_item.set_sensitive(
            False
        )

        idle_item.set_sensitive(
            False
        )

        low_battery_item.set_sensitive(
            False
        )

        indicator.set_title(
            "Razer Viper Ultimate déconnectée"
        )

        for item in stage_items:
            item.set_sensitive(False)

    def handle_disconnection() -> None:
        nonlocal previous_connection_state

        if previous_connection_state:
            print(
                "Mouse disconnected.",
                flush=True,
            )

        previous_connection_state = False
        set_disconnected_state()

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

        battery = state.battery
        is_charging = state.charging
        dpi_x = state.dpi
        active_stage = state.active_stage
        stages = state.stages
        idle_minutes = state.idle_minutes
        low_battery_threshold = state.low_battery_threshold
        charging_source = state.charging_source.value

        indicator.set_icon_full(
            str(
                tray_icon_dir
                / get_tray_icon(
                    battery,
                    is_charging,
                )
            ),
            f"Razer Viper Ultimate — "
            f"{battery:.0f} %",
        )

        battery_item.set_sensitive(
            True
        )

        dpi_item.set_sensitive(
            True
        )

        stage_item.set_sensitive(
            True
        )

        idle_item.set_sensitive(
            True
        )

        low_battery_item.set_sensitive(
            True
        )

        for item in stage_items:
            item.set_sensitive(
                True
            )

        name_item.label_widget.set_text(
            state.device_name
        )

        indicator.set_title(
            f"{state.device_name} — {battery:.0f} %"
        )

        mark_as_connected()

        battery_item.image_widget.set_from_file(
            str(
                menu_battery_icon_dir
                / get_battery_icon(
                    battery,
                    is_charging,
                )
            )
        )

        charge_estimation = get_charge_estimation(
            battery,
            charging_source,
            charge_models,
        )

        battery_text = (
            f"Batterie : {battery:.0f} %"
        )

        if is_charging and charge_estimation:
            battery_text += (
                f" ({charge_estimation})"
            )

        battery_item.label_widget.set_text(
            battery_text
        )

        dpi_item.label_widget.set_text(
            f"DPI : {dpi_x}"
        )

        stage_item.label_widget.set_text(
            f"Plage DPI : "
            f"{active_stage} / {len(stages)}"
        )

        for index, stage in enumerate(
            stages,
            start=1,
        ):
            item = stage_items[index - 1]

            item.set_label(
                f"{stage.x:>4}"
            )

            item.set_active(
                index == active_stage
            )

        idle_item.label_widget.set_text(
            f"Hibernation : {idle_minutes} min"
        )

        low_battery_item.label_widget.set_text(
            f"Basse consommation : "
            f"{low_battery_threshold} %"
        )

    # Create DPI Stage Items
    state = get_mouse_state()

    stages = state.stages

    stage_group = None

    for index, stage in enumerate(
        stages,
        start=1,
    ):
        item = Gtk.RadioMenuItem.new_with_label(
            stage_group,
            f"{stage.x:>4}",
        )

        stage_group = item.get_group()

        item.connect(
            "toggled",
            lambda item, stage=index:
                set_active_stage(stage)
                if item.get_active()
                else None,
        )

        stage_menu.append(item)
        stage_items.append(item)

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