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

        self.connected = True

    def poll(self) -> None:
        try:
            state = get_mouse_state()

        except Exception:
            self.handle_disconnected()
            return

        if not state.connected:
            self.handle_disconnected()
            return

        self.handle_connected(state)

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
    
    def handle_disconnected(self) -> None:
        if self.connected:
            print(
                "Mouse disconnected.",
                flush=True,
            )

        self.connected = False
        self.on_disconnected()


    def handle_connected(
        self,
        state: MouseState,
    ) -> None:
        if not self.connected:
            print(
                "Mouse reconnected.",
                flush=True,
            )

        self.connected = True
        self.on_connected(state)