import threading
from unittest.mock import MagicMock, patch

from razer.mouse_poller import MousePoller
from razer.mouse_state import MouseState


def _connected_state() -> MouseState:
    return MouseState(
        connected=True,
        device_name="Razer Viper Ultimate",
        battery=75.0,
        charging=False,
        charging_source=None,
        dpi=800,
        active_stage=1,
        stages=[800, 1600],
        idle_minutes=5,
        low_battery_threshold=15,
    )


def _disconnected_state() -> MouseState:
    return MouseState(
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


def test_poll_once_emits_connected_state() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    state = _connected_state()
    poller = MousePoller(on_connected, on_disconnected)

    with patch(
        "razer.mouse_poller.get_mouse_state",
        return_value=state,
    ):
        poller._poll_once()

    on_connected.assert_called_once_with(state)
    on_disconnected.assert_not_called()
    assert poller.connected


def test_poll_once_emits_disconnected_state() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    poller = MousePoller(on_connected, on_disconnected)

    with patch(
        "razer.mouse_poller.get_mouse_state",
        return_value=_disconnected_state(),
    ):
        poller._poll_once()

    on_connected.assert_not_called()
    on_disconnected.assert_called_once()
    assert not poller.connected


def test_poll_once_handles_get_mouse_state_exception_as_disconnection() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    poller = MousePoller(on_connected, on_disconnected)

    with patch(
        "razer.mouse_poller.get_mouse_state",
        side_effect=RuntimeError("D-Bus failure"),
    ):
        poller._poll_once()

    on_connected.assert_not_called()
    on_disconnected.assert_called_once()
    assert not poller.connected


def test_handle_state_calls_connected_callback_on_every_connected_state() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    state = _connected_state()
    poller = MousePoller(on_connected, on_disconnected)

    poller._handle_state(state)
    poller._handle_state(state)

    assert on_connected.call_count == 2
    on_disconnected.assert_not_called()
    assert poller.connected


def test_handle_state_calls_disconnected_callback_on_every_disconnected_state() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    poller = MousePoller(on_connected, on_disconnected)

    state = _disconnected_state()

    poller._handle_state(state)
    poller._handle_state(state)

    on_connected.assert_not_called()
    assert on_disconnected.call_count == 2
    assert not poller.connected


def test_handle_state_tracks_reconnection() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    connected_state = _connected_state()
    disconnected_state = _disconnected_state()
    poller = MousePoller(on_connected, on_disconnected)

    poller._handle_state(disconnected_state)
    poller._handle_state(connected_state)

    on_disconnected.assert_called_once()
    on_connected.assert_called_once_with(connected_state)
    assert poller.connected


def test_start_runs_polling_in_dedicated_thread() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    poller = MousePoller(on_connected, on_disconnected)

    poll_thread_id: int | None = None

    def get_state() -> MouseState:
        nonlocal poll_thread_id
        poll_thread_id = threading.get_ident()
        poller._stop_event.set()
        return _connected_state()

    with patch(
        "razer.mouse_poller.get_mouse_state",
        side_effect=get_state,
    ):
        poller.start()
        assert poller._thread is not None
        poller._thread.join()

    poller._thread = None

    assert poll_thread_id is not None
    assert poll_thread_id != threading.get_ident()


def test_start_does_not_start_second_thread_when_already_running() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    poller = MousePoller(on_connected, on_disconnected)

    poller._thread = MagicMock()
    poller._thread.is_alive.return_value = True

    with patch("razer.mouse_poller.Thread") as thread:
        poller.start()

    thread.assert_not_called()


def test_stop_stops_polling_thread() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    poller = MousePoller(on_connected, on_disconnected)

    thread = MagicMock()
    poller._thread = thread

    poller.stop()

    assert poller._stop_event.is_set()
    thread.join.assert_called_once()
    assert poller._thread is None
