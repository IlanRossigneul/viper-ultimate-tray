from pathlib import Path
from typing import Any

from KStatusNotifierItem import KStatusNotifierItem
from PySide6.QtCore import QRectF
from PySide6.QtGui import QAction, QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from battery.estimation import get_charge_estimation
from battery.icons import get_battery_icon, get_tray_icon
from razer.mouse_state import MouseState


class StatusView:
    def __init__(
        self,
        indicator: KStatusNotifierItem,
        menu_icon_dir: Path,
        tray_icon_dir: Path,
        menu_battery_icon_dir: Path,
        charge_models: dict[str, dict[str, Any]],
        name_item: QAction,
        battery_item: QAction,
        dpi_item: QAction,
        stage_item: QAction,
        idle_item: QAction,
        low_battery_item: QAction,
        stage_items: list[QAction],
        idle_items: list[QAction],
        low_battery_items: list[QAction],
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

        self.idle_items = idle_items

        self.low_battery_items = low_battery_items

    @staticmethod
    def load_svg_pixmap(path: Path) -> QPixmap:
        """Render an SVG file into a pixmap."""
        renderer = QSvgRenderer(str(path))

        if not renderer.isValid():
            raise ValueError(f"Invalid SVG icon: {path}")

        size = renderer.defaultSize()
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(0)

        painter = QPainter(image)
        renderer.render(painter, QRectF(image.rect()))
        painter.end()

        return QPixmap.fromImage(image)

    def show_disconnected(self) -> None:
        self.indicator.setIconByPixmap(QPixmap(str(self.menu_icon_dir / "mouse.svg")))

        self.name_item.setText("Razer Viper Ultimate déconnectée")

        self.battery_item.setText("Batterie : —")

        self.dpi_item.setText("DPI : —")

        self.stage_item.setText("Plage active : —")

        self.idle_item.setText("Hibernation : —")

        self.low_battery_item.setText("Basse consommation : —")

        for item in [
            self.battery_item,
            self.dpi_item,
            self.stage_item,
            self.idle_item,
            self.low_battery_item,
        ]:
            item.setEnabled(False)

        for item in self.stage_items:
            item.setEnabled(False)

        for item in self.idle_items:
            item.setEnabled(False)

        for item in self.low_battery_items:
            item.setEnabled(False)

        self.indicator.setTitle("Razer Viper Ultimate déconnectée")

    def show_connected(self, state: MouseState) -> None:
        battery = state.battery
        is_charging = state.charging

        if battery is None:
            self.indicator.setIconByPixmap(
                QPixmap(str(self.menu_icon_dir / "mouse.svg"))
            )

            self.name_item.setText(state.device_name)

            self.battery_item.setText("Batterie : —")

            return

        self.indicator.setIconByPixmap(
            self.load_svg_pixmap(
                self.tray_icon_dir / get_tray_icon(battery, is_charging)
            )
        )

        for item in [
            self.battery_item,
            self.dpi_item,
            self.stage_item,
            self.idle_item,
            self.low_battery_item,
        ]:
            item.setEnabled(True)

        for item in self.stage_items:
            item.setEnabled(True)

        for item in self.idle_items:
            item.setEnabled(True)

        for item in self.low_battery_items:
            item.setEnabled(True)

        self.name_item.setText(state.device_name)

        self.indicator.setTitle(f"{state.device_name} — {int(battery)} %")

        self.battery_item.setIcon(
            QIcon(
                str(self.menu_battery_icon_dir / get_battery_icon(battery, is_charging))
            )
        )

        charge_estimation = get_charge_estimation(
            battery,
            state.charging_source.value,
            self.charge_models,
        )

        battery_text = f"Batterie : {int(battery)} %"

        if is_charging and charge_estimation:
            battery_text += f" ({charge_estimation})"

        self.battery_item.setText(battery_text)

        self.dpi_item.setText(f"DPI : {state.dpi}")

        self.stage_item.setText(
            f"Plage DPI : {state.active_stage} / {len(state.stages)}"
        )

        for index, stage in enumerate(state.stages, start=1):
            item = self.stage_items[index - 1]

            item.setText(f"{stage:>4}")
            item.setChecked(index == state.active_stage)

        self.idle_item.setText(f"Hibernation : {state.idle_minutes} min")

        if state.idle_minutes is not None:
            for minutes, item in zip(
                range(15, 0, -1),
                self.idle_items,
            ):
                item.setChecked(minutes == state.idle_minutes)

        if state.low_battery_threshold is not None:
            for threshold, item in zip(
                range(25, 4, -5),
                self.low_battery_items,
            ):
                item.setChecked(threshold == state.low_battery_threshold)

        self.low_battery_item.setText(
            f"Basse consommation : {state.low_battery_threshold} %"
        )
