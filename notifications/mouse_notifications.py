from pathlib import Path

import gi

gi.require_version("Notify", "0.7")

from gi.repository import GLib, Notify

from razer.mouse_state import MouseState


BATTERY_ICON_DIR = (
    Path(__file__).resolve().parent.parent
    / "icons"
    / "menu"
    / "battery"
)

LOW_BATTERY_ICON_PATH = BATTERY_ICON_DIR / "battery-2.svg"
VERY_LOW_BATTERY_ICON_PATH = BATTERY_ICON_DIR / "battery-1.svg"
EXTREMELY_LOW_BATTERY_ICON_PATH = BATTERY_ICON_DIR / "battery-0.svg"
FULL_BATTERY_ICON_PATH = BATTERY_ICON_DIR / "battery-charging-4.svg"


class MouseNotificationManager:
    def __init__(self) -> None:
        Notify.init("Viper Ultimate Tray")

        self._previous_state: MouseState | None = None

        self._low_battery_notified = False
        self._very_low_battery_notified = False
        self._extremely_low_battery_notified = False
        self._charge_complete_notified = False

    def update(self, state: MouseState) -> None:
        previous_state = self._previous_state

        if previous_state is None:
            self._previous_state = state
            return

        if not state.connected:
            self._previous_state = state
            return

        self._handle_battery_notifications(previous_state, state)

        self._handle_charge_notification(previous_state, state)

        self._previous_state = state

    def reset(self) -> None:
        self._previous_state = None

        self._low_battery_notified = False
        self._very_low_battery_notified = False
        self._extremely_low_battery_notified = False
        self._charge_complete_notified = False

    def _handle_battery_notifications(
        self,
        previous_state: MouseState,
        state: MouseState,
    ) -> None:
        if state.battery is None:
            return

        # Re-arm each low-battery notification once the battery
        # level rises above its corresponding threshold.
        if state.battery > 30:
            self._low_battery_notified = False

        if state.battery > 15:
            self._very_low_battery_notified = False

        if state.battery > 5:
            self._extremely_low_battery_notified = False

        if state.charging is not False:
            return

        previous_battery = previous_state.battery

        if previous_battery is None:
            return

        if (
            previous_battery > 30
            and state.battery <= 30
            and not self._low_battery_notified
        ):
            self._notify(
                state,
                "Batterie faible — 30 %",
                LOW_BATTERY_ICON_PATH,
                "dialog-warning",
            )

            self._low_battery_notified = True

        if (
            previous_battery > 15
            and state.battery <= 15
            and not self._very_low_battery_notified
        ):
            self._notify(
                state,
                "Batterie faible — 15 %",
                VERY_LOW_BATTERY_ICON_PATH,
                "battery-low",
            )

            self._very_low_battery_notified = True

        if (
            previous_battery > 5
            and state.battery <= 5
            and not self._extremely_low_battery_notified
        ):
            self._notify(
                state,
                "Batterie faible — 5 %",
                EXTREMELY_LOW_BATTERY_ICON_PATH,
                "battery-caution",
            )

            self._extremely_low_battery_notified = True

    def _handle_charge_notification(
        self,
        previous_state: MouseState,
        state: MouseState,
    ) -> None:
        # Re-arm the charge-complete notification as soon as
        # charging stops.
        if state.charging is False:
            self._charge_complete_notified = False

        if state.battery is None or state.charging is not True:
            return

        previous_battery = previous_state.battery

        if previous_battery is None:
            return

        if (
            previous_battery < 100
            and state.battery >= 100
            and not self._charge_complete_notified
        ):
            self._notify(
                state,
                "Charge terminée — batterie à 100 %",
                FULL_BATTERY_ICON_PATH,
                "battery-full",
            )

            self._charge_complete_notified = True

    def _notify(
        self,
        state: MouseState,
        message: str,
        icon_path: Path,
        sound_name: str,
    ) -> None:
        notification = Notify.Notification.new(
            f"🖱️ {state.device_name}",
            message,
            str(icon_path),
        )

        notification.set_timeout(10000)

        notification.set_hint(
            "desktop-entry",
            GLib.Variant("s", "viper-ultimate-tray"),
        )

        notification.set_hint(
            "sound-name",
            GLib.Variant("s", sound_name),
        )

        notification.show()
