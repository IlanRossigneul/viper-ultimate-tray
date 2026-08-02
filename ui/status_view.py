from battery.icons import (
    get_battery_icon,
    get_tray_icon,
)

from battery.estimation import (
    get_charge_estimation,
)


class StatusView:
    def __init__(
        self,
        indicator,
        icon_dir,
        tray_icon_dir,
        menu_battery_icon_dir,
        charge_models,
        name_item,
        battery_item,
        dpi_item,
        stage_item,
        idle_item,
        low_battery_item,
        stage_items,
    ):
        self.indicator = indicator

        self.icon_dir = icon_dir
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

    def show_disconnected(self):
        self.indicator.set_icon_full(
            str(self.icon_dir / "mouse.svg"),
            "Razer Viper Ultimate",
        )

        self.name_item.label_widget.set_text(
            "Razer Viper Ultimate déconnectée"
        )

        self.battery_item.label_widget.set_text(
            "Batterie : —"
        )

        self.dpi_item.label_widget.set_text(
            "DPI : —"
        )

        self.stage_item.label_widget.set_text(
            "Plage active : —"
        )

        self.idle_item.label_widget.set_text(
            "Hibernation : —"
        )

        self.low_battery_item.label_widget.set_text(
            "Basse consommation : —"
        )

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

        self.indicator.set_title(
            "Razer Viper Ultimate déconnectée"
        )

    def show_connected(
        self,
        state,
    ):
        battery = state.battery
        is_charging = state.charging

        self.indicator.set_icon_full(
            str(
                self.tray_icon_dir
                / get_tray_icon(
                    battery,
                    is_charging,
                )
            ),
            f"Razer Viper Ultimate — "
            f"{battery:.0f} %",
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

        self.name_item.label_widget.set_text(
            state.device_name
        )

        self.indicator.set_title(
            f"{state.device_name} — {battery:.0f} %"
        )

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

        battery_text = (
            f"Batterie : {battery:.0f} %"
        )

        if is_charging and charge_estimation:
            battery_text += (
                f" ({charge_estimation})"
            )

        self.battery_item.label_widget.set_text(
            battery_text
        )

        self.dpi_item.label_widget.set_text(
            f"DPI : {state.dpi}"
        )

        self.stage_item.label_widget.set_text(
            f"Plage DPI : "
            f"{state.active_stage} / "
            f"{len(state.stages)}"
        )

        for index, stage in enumerate(
            state.stages,
            start=1,
        ):
            item = self.stage_items[index - 1]

            item.set_label(
                f"{stage.x:>4}"
            )

            item.set_active(
                index == state.active_stage
            )

        self.idle_item.label_widget.set_text(
            f"Hibernation : "
            f"{state.idle_minutes} min"
        )

        self.low_battery_item.label_widget.set_text(
            f"Basse consommation : "
            f"{state.low_battery_threshold} %"
        )