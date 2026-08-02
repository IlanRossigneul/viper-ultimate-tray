from collections.abc import Callable

from gi.repository import GLib

from razer.mouse_state import (
    MouseState,
    get_mouse_state,
)


class MousePoller:
    def __init__(
        self,
        on_connected: Callable[[MouseState], None],
        on_disconnected: Callable[[], None],
    ):
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected

    def poll(self) -> None:
        try:
            state = get_mouse_state()

        except Exception:
            self.on_disconnected()
            return

        if not state.connected:
            self.on_disconnected()
            return

        self.on_connected(state)

    def start(
        self,
        interval: int = 2000,
    ) -> None:
        def refresh():
            self.poll()
            return True

        GLib.timeout_add(
            interval,
            refresh,
        )