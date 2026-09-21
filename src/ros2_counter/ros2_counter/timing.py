"""GUI-independent counter and publisher-timestamp timing primitives."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, median, pstdev
from typing import Protocol

UINT32_MODULUS = 1 << 32


class RosStamp(Protocol):
    sec: int
    nanosec: int


def stamp_to_seconds(stamp: RosStamp) -> float:
    """Convert a ROS builtin_interfaces/Time-like value to seconds."""
    return float(stamp.sec) + float(stamp.nanosec) / 1_000_000_000.0


def interval_seconds(current: RosStamp, previous: RosStamp) -> float:
    """Return current minus previous publisher timestamp in seconds."""
    sec_delta = int(current.sec) - int(previous.sec)
    nanosec_delta = int(current.nanosec) - int(previous.nanosec)
    return float(sec_delta) + float(nanosec_delta) / 1_000_000_000.0


class CounterSequence:
    """Generate uint32 counter values, beginning with zero."""

    def __init__(self, initial: int = 0) -> None:
        if not 0 <= initial < UINT32_MODULUS:
            raise ValueError("initial counter must fit in uint32")
        self._next = initial

    def take(self) -> int:
        value = self._next
        self._next = (value + 1) % UINT32_MODULUS
        return value


@dataclass(frozen=True)
class TimingSnapshot:
    latest_count: int | None
    latest_timestamp: float | None
    latest_period: float | None
    intervals: tuple[float, ...]
    sample_indices: tuple[int, ...]
    means: tuple[float, ...]
    medians: tuple[float, ...]
    standard_deviations: tuple[float, ...]


class TimingState:
    """Accumulate valid consecutive publisher-stamp intervals and statistics."""

    def __init__(self) -> None:
        self._previous_stamp: RosStamp | None = None
        self._latest_count: int | None = None
        self._latest_timestamp: float | None = None
        self._latest_period: float | None = None
        self._intervals: list[float] = []
        self._means: list[float] = []
        self._medians: list[float] = []
        self._standard_deviations: list[float] = []

    def observe(self, count: int, stamp: RosStamp) -> tuple[TimingSnapshot, bool]:
        """Observe a sample, returning its snapshot and whether timing was valid."""
        if not 0 <= count < UINT32_MODULUS:
            raise ValueError("count must fit in uint32")

        period = None
        valid = True
        if self._previous_stamp is not None:
            period = interval_seconds(stamp, self._previous_stamp)
            valid = period >= 0.0
            if valid:
                self._intervals.append(period)
                self._means.append(fmean(self._intervals))
                self._medians.append(median(self._intervals))
                self._standard_deviations.append(pstdev(self._intervals))

        self._previous_stamp = stamp
        self._latest_count = count
        self._latest_timestamp = stamp_to_seconds(stamp)
        self._latest_period = period
        return self.snapshot(), valid

    def snapshot(self) -> TimingSnapshot:
        length = len(self._intervals)
        return TimingSnapshot(
            latest_count=self._latest_count,
            latest_timestamp=self._latest_timestamp,
            latest_period=self._latest_period,
            intervals=tuple(self._intervals),
            sample_indices=tuple(range(1, length + 1)),
            means=tuple(self._means),
            medians=tuple(self._medians),
            standard_deviations=tuple(self._standard_deviations),
        )
