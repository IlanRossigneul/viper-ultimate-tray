import logging
import time
from dataclasses import dataclass, replace
from enum import Enum
from threading import RLock

from openrazer.client import DeviceManager
from openrazer.client.devices.mice import RazerMouse

from razer.device import (
    create_device_manager,
    find_viper_ultimate_device,
    get_charging_source,
)

logger = logging.getLogger(__name__)


class ChargingSource(Enum):
    WIRED = "wired"
    WIRELESS = "wireless"


@dataclass(slots=True)
class DPIStage:
    dpi: int


@dataclass(slots=True)
class MouseState:
    connected: bool

    device_name: str | None

    battery: float | None
    charging: bool | None
    charging_source: ChargingSource | None

    dpi: tuple[int, int] | None

    active_stage: int | None
    stages: list[DPIStage]

    idle_minutes: int | None
    low_battery_threshold: int | None


def _get_disconnected_state() -> MouseState:
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


class MousePollingSession:
    """Reuse OpenRazer objects and cache values that rarely change."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._device_manager: DeviceManager | None = None
        self._mouse: RazerMouse | None = None

        self._device_name: str | None = None
        self._charging_source: ChargingSource | None = None
        self._dpi: tuple[int, int] | None = None
        self._active_stage: int | None = None
        self._raw_stages: list[tuple[int, int]] = []
        self._stages: list[DPIStage] = []
        self._idle_minutes: int | None = None
        self._low_battery_threshold: int | None = None
        self._last_state = _get_disconnected_state()
        self._connection_generation = 0
        self._hibernating = False

    @property
    def connection_generation(self) -> int:
        with self._lock:
            return self._connection_generation

    def seed_state(self, state: MouseState) -> None:
        """Seed cached values without retaining a D-Bus object across threads."""
        with self._lock:
            self._device_name = state.device_name
            self._charging_source = state.charging_source
            self._dpi = state.dpi
            self._active_stage = state.active_stage
            self._stages = list(state.stages)
            self._raw_stages = [(stage.dpi, stage.dpi) for stage in state.stages]
            self._idle_minutes = state.idle_minutes
            self._low_battery_threshold = state.low_battery_threshold
            self._last_state = replace(state, stages=list(state.stages))
            self._hibernating = (
                state.connected and state.battery is None and state.charging is False
            )

    def get_cached_state(self) -> MouseState:
        """Return the latest state without making D-Bus calls."""
        with self._lock:
            return replace(self._last_state, stages=list(self._last_state.stages))

    def _invalidate(self) -> None:
        self._device_manager = None
        self._mouse = None
        self._device_name = None
        self._charging_source = None
        self._idle_minutes = None
        self._low_battery_threshold = None
        self._last_state = _get_disconnected_state()
        self._hibernating = False

    def _connect(self) -> bool:
        try:
            manager = create_device_manager()
            mouse = find_viper_ultimate_device(manager)
        except Exception:  # noqa: BLE001
            self._invalidate()
            return False

        if mouse is None:
            self._invalidate()
            return False

        try:
            self._device_manager = manager
            self._mouse = mouse
            self._device_name = mouse.name
            self._charging_source = ChargingSource(get_charging_source(mouse))
            self._dpi = mouse.dpi

            if self._idle_minutes is None:
                self._idle_minutes = mouse.get_idle_time() // 60

            if self._low_battery_threshold is None:
                self._low_battery_threshold = mouse.get_low_battery_threshold()
        except Exception:  # noqa: BLE001
            self._invalidate()
            return False

        self._connection_generation += 1
        return True

    def get_state(self) -> MouseState:
        started_at = time.perf_counter()
        with self._lock:
            new_connection = self._mouse is None
            if new_connection and not self._connect():
                logger.debug(
                    "Mouse polling: mode=disconnected reason=connection_failed "
                    "total=%.2f ms",
                    (time.perf_counter() - started_at) * 1000,
                )
                return _get_disconnected_state()

            mouse = self._mouse
            if mouse is None:
                logger.debug(
                    "Mouse polling: mode=disconnected reason=no_mouse total=%.2f ms",
                    (time.perf_counter() - started_at) * 1000,
                )
                return _get_disconnected_state()

            try:
                battery_started_at = time.perf_counter()
                battery = mouse._dbus_interfaces["power"].getBattery()
                battery_duration = time.perf_counter() - battery_started_at

                if self._hibernating and battery in (0.0, -1.0):
                    state = replace(
                        self._last_state,
                        battery=None,
                        charging=False,
                        stages=list(self._last_state.stages),
                    )
                    self._last_state = state
                    logger.debug(
                        "Mouse polling: mode=hibernating battery=%.2f ms total=%.2f ms",
                        battery_duration * 1000,
                        (time.perf_counter() - started_at) * 1000,
                    )
                    return state

                charging_started_at = time.perf_counter()
                charging = mouse.is_charging
                charging_duration = time.perf_counter() - charging_started_at

                if battery == -1.0:
                    battery = None
                elif battery == 0.0:
                    battery = 0 if charging else None

                stages_started_at = time.perf_counter()
                active_stage, raw_stages = mouse.dpi_stages
                stages_duration = time.perf_counter() - stages_started_at
                stages = [DPIStage(dpi=dpi_x) for dpi_x, _ in raw_stages]
            except Exception:
                logger.exception("Failed to read mouse state from OpenRazer.")
                self._invalidate()
                logger.debug(
                    "Mouse polling: mode=disconnected reason=read_failed total=%.2f ms",
                    (time.perf_counter() - started_at) * 1000,
                )
                return _get_disconnected_state()

            if (
                not new_connection
                and self._active_stage is not None
                and active_stage != self._active_stage
                and 1 <= active_stage <= len(raw_stages)
            ):
                self._dpi = raw_stages[active_stage - 1]

            self._active_stage = active_stage
            self._raw_stages = list(raw_stages)
            self._stages = stages

            state = MouseState(
                connected=True,
                device_name=self._device_name,
                battery=battery,
                charging=charging,
                charging_source=self._charging_source,
                dpi=self._dpi,
                active_stage=active_stage,
                stages=list(stages),
                idle_minutes=self._idle_minutes,
                low_battery_threshold=self._low_battery_threshold,
            )
            self._last_state = state
            self._hibernating = battery is None and charging is False
            logger.debug(
                "Mouse polling: mode=active battery=%.2f ms charging=%.2f ms "
                "dpi_stages=%.2f ms total=%.2f ms",
                battery_duration * 1000,
                charging_duration * 1000,
                stages_duration * 1000,
                (time.perf_counter() - started_at) * 1000,
            )
            return state

    def update_dpi(self, dpi: tuple[int, int]) -> None:
        with self._lock:
            self._dpi = dpi
            self._last_state = replace(self._last_state, dpi=dpi)

    def update_dpi_stages(
        self,
        stages: list[DPIStage],
        active_stage: int,
    ) -> None:
        with self._lock:
            self._stages = list(stages)
            self._raw_stages = [(stage.dpi, stage.dpi) for stage in stages]
            self._active_stage = active_stage
            if 1 <= active_stage <= len(self._raw_stages):
                self._dpi = self._raw_stages[active_stage - 1]
            self._last_state = replace(
                self._last_state,
                dpi=self._dpi,
                active_stage=active_stage,
                stages=list(self._stages),
            )

    def update_active_stage(self, active_stage: int) -> None:
        with self._lock:
            self._active_stage = active_stage
            if 1 <= active_stage <= len(self._raw_stages):
                self._dpi = self._raw_stages[active_stage - 1]
            self._last_state = replace(
                self._last_state,
                dpi=self._dpi,
                active_stage=active_stage,
            )

    def update_idle_minutes(self, minutes: int) -> None:
        with self._lock:
            self._idle_minutes = minutes
            self._last_state = replace(self._last_state, idle_minutes=minutes)

    def update_low_battery_threshold(self, threshold: int) -> None:
        with self._lock:
            self._low_battery_threshold = threshold
            self._last_state = replace(
                self._last_state,
                low_battery_threshold=threshold,
            )


def get_mouse_state() -> MouseState:
    """Read a one-off mouse state, primarily for startup and UI refreshes."""
    return MousePollingSession().get_state()
