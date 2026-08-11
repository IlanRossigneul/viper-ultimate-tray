from pathlib import Path
from typing import Any

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")

from gi.repository import AppIndicator3, Gtk

from battery.estimation import get_charge_estimation
from battery.icons import get_battery_icon, get_tray_icon
from razer.mouse_state import MouseState


class StatusView:
    def __init__(
        self,
        indicator: AppIndicator3.Indicator,
        menu_icon_dir: Path,
        tray_icon_dir: Path,
        menu_battery_icon_dir: Path,
        charge_models: dict[str, dict[str, Any]],
        name_item: Gtk.MenuItem,
        battery_item: Gtk.MenuItem,
        dpi_item: Gtk.MenuItem,
        stage_item: Gtk.MenuItem,
        idle_item: Gtk.MenuItem,
        low_battery_item: Gtk.MenuItem,
        stage_items: list[Gtk.RadioMenuItem],
    ):
        self.indicator = indicator

        self.menu_icon_dir = menu_icon_dir
        self.tray_icon_dir = tray_icon_dir
        self.menu_battery_icon_dir = menu_battery_icon_dir

        self.charge_models = charge_models

        self.name_item = name_item
        self.battery_item = battery_item
        self.dpi_item = dpi_item
        self.stage_item = stage_item
        self.idle_item = idle_item
        self.low_battery_item = low_battery_item

        self.stage_items = stage_items

    def show_disconnected(self) -> None:
        self.indicator.set_icon_full(str(self.menu_icon_dir / "mouse.svg"), "Razer Viper Ultimate")

        self.name_item.label_widget.set_text("Razer Viper Ultimate déconnectée")

        self.battery_item.label_widget.set_text("Batterie : —")

        self.dpi_item.label_widget.set_text("DPI : —")

        self.stage_item.label_widget.set_text("Plage active : —")

        self.idle_item.label_widget.set_text("Hibernation : —")

        self.low_battery_item.label_widget.set_text("Basse consommation : —")

        for item in [
            self.battery_item,
            self.dpi_item,
            self.stage_item,
            self.idle_item,
            self.low_battery_item,
        ]:
            item.set_sensitive(False)

        for item in self.stage_items:
            item.set_sensitive(False)

        self.indicator.set_title("Razer Viper Ultimate déconnectée")

    def show_connected(
        self,
        state: MouseState,
    ) -> None:
        battery = state.battery
        is_charging = state.charging

        if battery is None:
            self.indicator.set_icon_full(
                str(self.menu_icon_dir / "mouse.svg"),
                f"{state.device_name} — Batterie indisponible",
            )

            self.name_item.label_widget.set_text(state.device_name)

            self.battery_item.label_widget.set_text("Batterie : —")

            return

        self.indicator.set_icon_full(
            str(
                self.tray_icon_dir
                / get_tray_icon(
                    battery,
                    is_charging,
                )
            ),
            f"{state.device_name} — {battery:.0f} %",
        )

        for item in [
            self.battery_item,
            self.dpi_item,
            self.stage_item,
            self.idle_item,
            self.low_battery_item,
        ]:
            item.set_sensitive(True)

        for item in self.stage_items:
            item.set_sensitive(True)

        self.name_item.label_widget.set_text(state.device_name)

        self.indicator.set_title(f"{state.device_name} — {battery:.0f} %")

        self.battery_item.image_widget.set_from_file(
            str(
                self.menu_battery_icon_dir
                / get_battery_icon(
                    battery,
                    is_charging,
                )
            )
        )

        charge_estimation = get_charge_estimation(
            battery,
            state.charging_source.value,
            self.charge_models,
        )

        battery_text = f"Batterie : {battery:.0f} %"

        if is_charging and charge_estimation:
            battery_text += f" ({charge_estimation})"

        self.battery_item.label_widget.set_text(battery_text)

        self.dpi_item.label_widget.set_text(f"DPI : {state.dpi}")

        self.stage_item.label_widget.set_text(
            f"Plage DPI : "
            f"{state.active_stage} / "
            f"{len(state.stages)}"
        )

        for index, stage in enumerate(state.stages, start=1):
            item = self.stage_items[index - 1]

            item.set_label(f"{stage.x:>4}")

            item.set_active(index == state.active_stage)

        self.idle_item.label_widget.set_text(f"Hibernation : {state.idle_minutes} min")

        self.low_battery_item.label_widget.set_text(
            f"Basse consommation : {state.low_battery_threshold} %"
        )