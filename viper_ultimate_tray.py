import json
import subprocess
import sys
from pathlib import Path

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

import openrazer.client


def main() -> int:
    icon_dir = ICON_DIR

    menu_icon_dir = MENU_ICON_DIR

    menu_battery_icon_dir = MENU_BATTERY_ICON_DIR

    tray_icon_dir = TRAY_ICON_DIR

    model_file = MODEL_FILE

    device_manager = (
        openrazer.client.DeviceManager()
    )

    with model_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        charge_models = json.load(file)["sources"]

    def find_viper_ultimate_device(manager):
        return next(
            (
                device
                for device in manager.devices
                if device.name.startswith(
                    "Razer Viper Ultimate"
                )
            ),
            None,
        )

    def create_menu_item(
        icon_path: Path | None = None,
        text: str = "",
    ) -> Gtk.MenuItem:
        item = Gtk.MenuItem()

        box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
        )

        if icon_path:
            image = Gtk.Image.new_from_file(
                str(icon_path)
            )

            box.pack_start(
                image,
                False,
                False,
                0,
            )

        label = Gtk.Label(
            label=text,
            xalign=0,
        )

        box.pack_start(
            label,
            True,
            True,
            0,
        )

        item.add(box)

        item.label_widget = label
        item.image_widget = (
            image
            if icon_path
            else None
        )

        item.show_all()

        return item

    def add_separator(
        menu: Gtk.Menu,
    ) -> None:
        separator = Gtk.SeparatorMenuItem()
        separator.show()

        menu.append(
            separator
        )

    def get_charging_source(device) -> str:
        if "(Wired)" in device._name:
            return "wired"

        return "wireless"

    viper = find_viper_ultimate_device(
        device_manager
    )
    mouse_connected = True

    if viper is None:
        print(
            "Razer Viper Ultimate not detected.",
            flush=True,
        )
        return 1

    indicator = AppIndicator3.Indicator.new(
        "viper-ultimate-tray",
        str(icon_dir / "mouse.svg"),
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )

    indicator.set_status(
        AppIndicator3.IndicatorStatus.ACTIVE
    )

    menu = Gtk.Menu()

    # Create the main menu
    name_item = create_menu_item(
        menu_icon_dir / "mouse.svg",
        viper.name,
    )

    battery_item = create_menu_item(
        menu_battery_icon_dir / "battery-4.svg",
    )

    dpi_item = create_menu_item(
        menu_icon_dir / "dpi.svg",
    )

    stage_item = create_menu_item(
        menu_icon_dir / "stages-dpi.svg",
    )

    idle_item = create_menu_item(
        menu_icon_dir / "hibernation.svg",
    )

    low_battery_item = create_menu_item(
        menu_icon_dir / "low-conso.svg",
    )

    stage_menu = Gtk.Menu()

    stage_item.set_submenu(
        stage_menu
    )

    stage_items = []

    polychromatic_action = create_menu_item(
        menu_icon_dir / "polychromatic.svg",
        "Ouvrir Polychromatic",
    )

    polychromatic_action.connect(
        "activate",
        lambda *_:
            subprocess.Popen(
                ["polychromatic-controller"],
                start_new_session=True,
            ),
    )

    input_remapper_action = create_menu_item(
        menu_icon_dir / "input-remapper.svg",
        "Ouvrir Input Remapper",
    )

    input_remapper_action.connect(
        "activate",
        lambda *_:
            subprocess.Popen(
                ["input-remapper-gtk"],
                start_new_session=True,
            ),
    )

    quit_action = create_menu_item(
        text="Quitter",
    )

    quit_action.connect(
        "activate",
        lambda *_:
            Gtk.main_quit(),
    )

    menu.append(name_item)

    add_separator(menu)

    menu.append(battery_item)

    add_separator(menu)

    menu.append(dpi_item)
    menu.append(stage_item)

    add_separator(menu)

    menu.append(idle_item)
    menu.append(low_battery_item)

    add_separator(menu)

    menu.append(polychromatic_action)
    menu.append(input_remapper_action)

    add_separator(menu)

    menu.append(quit_action)

    def set_active_stage(stage_number: int) -> None:
        if viper is None:
            return

        try:
            _, stages = viper.dpi_stages

            viper.dpi_stages = (
                stage_number,
                stages,
            )

            update_mouse_status()

        except Exception as error:
            print(
                f"Failed to change the DPI stage: "
                f"{error}",
                flush=True,
            )

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
        nonlocal viper, mouse_connected

        if mouse_connected:
            print(
                "Mouse disconnected.",
                flush=True,
            )

        mouse_connected = False
        viper = None
        set_disconnected_state()

    def mark_as_connected() -> None:
        nonlocal mouse_connected

        if not mouse_connected:
            print(
                "Mouse reconnected.",
                flush=True,
            )

        mouse_connected = True

    def update_mouse_status() -> None:
        nonlocal viper

        try:
            # Recreate the device manager intentionally to detect
            # state changes between wireless and wired modes.
            current_device_manager = (
                openrazer.client.DeviceManager()
            )

            current_viper = find_viper_ultimate_device(
                current_device_manager
            )

        except Exception:
            handle_disconnection()
            return

        if current_viper is None:
            handle_disconnection()
            return

        viper = current_viper

        charging_source = get_charging_source(viper)

        try:
            battery = viper.battery_level
            is_charging = viper.is_charging
            dpi_x, _ = viper.dpi
            active_stage, stages = viper.dpi_stages
            idle_minutes = viper.get_idle_time() // 60
            low_battery_threshold = (
                viper.get_low_battery_threshold()
            )

        except Exception:
            handle_disconnection()
            return

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
            viper.name
        )

        indicator.set_title(
            f"{viper.name} — {battery:.0f} %"
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

        for index, (stage_dpi_x, _) in enumerate(
            stages,
            start=1,
        ):
            item = stage_items[index - 1]

            item.set_label(
                f"{stage_dpi_x:>4}"
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
    _, stages = viper.dpi_stages

    stage_group = None

    for index, (dpi_x, _) in enumerate(
        stages,
        start=1,
    ):
        item = Gtk.RadioMenuItem.new_with_label(
            stage_group,
            f"{dpi_x:>4}",
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