import logging
from collections.abc import Callable

from PySide6.QtCore import QTimer

from razer.mouse_state import MouseState, get_mouse_state

logger = logging.getLogger(__name__)


class MousePoller:
    def __init__(
        self,
        on_connected: Callable[[MouseState], None],
        on_disconnected: Callable[[], None],
    ):
        self.on_connected: Callable[[MouseState], None] = on_connected
        self.on_disconnected: Callable[[], None] = on_disconnected

        self.connected: bool = True

        self.timer = QTimer()
        self.timer.timeout.connect(self.poll)

    def poll(self) -> None:
        try:
            state = get_mouse_state()

        except Exception:  # noqa: BLE001
            self._handle_disconnected()
            return

        if not state.connected:
            self._handle_disconnected()
            return

        self._handle_connected(state)

    def start(self, interval: int = 2000) -> None:
        self.timer.start(interval)

    def _handle_disconnected(self) -> None:
        if self.connected:
            logger.info("Mouse disconnected.")

        self.connected = False
        self.on_disconnected()

    def _handle_connected(self, state: MouseState) -> None:
        if not self.connected:
            logger.info("Mouse reconnected.")

        self.connected = True
        self.on_connected(state)
