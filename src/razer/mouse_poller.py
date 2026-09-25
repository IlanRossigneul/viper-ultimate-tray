import logging
from collections.abc import Callable
from threading import Event, Thread

from PySide6.QtCore import QObject, Signal

from razer.mouse_state import MouseState, get_mouse_state

logger = logging.getLogger(__name__)


class MousePoller(QObject):
    state_ready = Signal(MouseState)

    def __init__(
        self,
        on_connected: Callable[[MouseState], None],
        on_disconnected: Callable[[], None],
    ) -> None:
        super().__init__()

        self.on_connected = on_connected
        self.on_disconnected = on_disconnected

        self.connected = True

        self._stop_event = Event()
        self._thread: Thread | None = None
        self._interval_seconds = 2.0

        self.state_ready.connect(self._handle_state)

    def start(self, interval: int = 2000) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._interval_seconds = interval / 1000
        self._stop_event.clear()

        self._thread = Thread(
            target=self._run,
            daemon=True,
            name="MousePoller",
        )
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return

        self._stop_event.set()
        self._thread.join()

        self._thread = None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._poll_once()

            if self._stop_event.wait(self._interval_seconds):
                break

    def _poll_once(self) -> None:
        try:
            state = get_mouse_state()
        except Exception:
            logger.exception("Failed to poll mouse state.")
            state = MouseState(
                connected=False,
                device_name=None,
                battery=None,
                charging=None,
                charging_source=None,
                dpi=None,
                active_stage=None,
                stages=[],
                idle_minutes=None,
                low_battery_threshold=None,
            )

        self.state_ready.emit(state)

    def _handle_state(self, state: MouseState) -> None:
        if not state.connected:
            self._handle_disconnected()
            return

        self._handle_connected(state)

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
