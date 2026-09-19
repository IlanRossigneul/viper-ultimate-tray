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


def test_poll_calls_connected_callback_with_current_state() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    state = _connected_state()

    poller = MousePoller(on_connected, on_disconnected)

    with patch(
        "razer.mouse_poller.get_mouse_state",
        return_value=state,
    ):
        poller.poll()

    on_connected.assert_called_once_with(state)
    on_disconnected.assert_not_called()
    assert poller.connected


def test_poll_calls_disconnected_callback_when_state_is_disconnected() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    poller = MousePoller(on_connected, on_disconnected)

    with patch(
        "razer.mouse_poller.get_mouse_state",
        return_value=_disconnected_state(),
    ):
        poller.poll()

    on_connected.assert_not_called()
    on_disconnected.assert_called_once()
    assert not poller.connected


def test_poll_handles_get_mouse_state_exception_as_disconnection() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    poller = MousePoller(on_connected, on_disconnected)

    with patch(
        "razer.mouse_poller.get_mouse_state",
        side_effect=RuntimeError("D-Bus failure"),
    ):
        poller.poll()

    on_connected.assert_not_called()
    on_disconnected.assert_called_once()
    assert not poller.connected


def test_poll_calls_connected_callback_on_every_connected_poll() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    state = _connected_state()
    poller = MousePoller(on_connected, on_disconnected)

    with patch(
        "razer.mouse_poller.get_mouse_state",
        return_value=state,
    ):
        poller.poll()
        poller.poll()

    assert on_connected.call_count == 2
    on_disconnected.assert_not_called()
    assert poller.connected


def test_poll_calls_disconnected_callback_on_every_disconnected_poll() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    poller = MousePoller(on_connected, on_disconnected)

    with patch(
        "razer.mouse_poller.get_mouse_state",
        return_value=_disconnected_state(),
    ):
        poller.poll()
        poller.poll()

    on_connected.assert_not_called()
    assert on_disconnected.call_count == 2
    assert not poller.connected


def test_poll_tracks_reconnection() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    connected_state = _connected_state()
    disconnected_state = _disconnected_state()
    poller = MousePoller(on_connected, on_disconnected)

    with patch(
        "razer.mouse_poller.get_mouse_state",
        side_effect=[disconnected_state, connected_state],
    ):
        poller.poll()
        poller.poll()

    on_disconnected.assert_called_once()
    on_connected.assert_called_once_with(connected_state)
    assert poller.connected


def test_start_starts_timer_with_default_interval() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    poller = MousePoller(on_connected, on_disconnected)

    with patch.object(poller.timer, "start") as start:
        poller.start()

    start.assert_called_once_with(2000)


def test_start_starts_timer_with_custom_interval() -> None:
    on_connected = MagicMock()
    on_disconnected = MagicMock()
    poller = MousePoller(on_connected, on_disconnected)

    with patch.object(poller.timer, "start") as start:
        poller.start(5000)

    start.assert_called_once_with(5000)
