"""Widget-independent counter and publisher-time statistics."""

from dataclasses import dataclass
from heapq import heappop, heappush
from math import sqrt

UINT32_MODULUS = 1 << 32


def next_count(count: int) -> int:
    return (count + 1) % UINT32_MODULUS


def stamp_seconds(stamp) -> float:
    return stamp.sec + stamp.nanosec / 1_000_000_000


def stamp_nanoseconds(stamp) -> int:
    return stamp.sec * 1_000_000_000 + stamp.nanosec


@dataclass(frozen=True)
class Sample:
    index: int
    count: int
    stamp: str
    period: float | None
    invalid_period: bool
    mean: float | None
    median: float | None
    stddev: float | None


class TimingModel:
    def __init__(self):
        self.previous_stamp = None
        self.periods = []
        self.history = []
        self.sample_index = 0
        self._lower = []  # Negated values, forming a max heap.
        self._upper = []
        self._mean = 0.0
        self._sum_squared_deviations = 0.0

    def _add_period(self, period):
        self.periods.append(period)
        count = len(self.periods)
        delta = period - self._mean
        self._mean += delta / count
        self._sum_squared_deviations += delta * (period - self._mean)

        if not self._lower or period <= -self._lower[0]:
            heappush(self._lower, -period)
        else:
            heappush(self._upper, period)
        if len(self._lower) > len(self._upper) + 1:
            heappush(self._upper, -heappop(self._lower))
        elif len(self._upper) > len(self._lower):
            heappush(self._lower, -heappop(self._upper))

    def _median(self):
        if len(self._lower) == len(self._upper):
            return (-self._lower[0] + self._upper[0]) / 2
        return -self._lower[0]

    def observe(self, count: int, stamp) -> Sample:
        current = stamp_nanoseconds(stamp)
        period = None if self.previous_stamp is None else (
            current - self.previous_stamp
        ) / 1_000_000_000
        # Advance even after a clock jump; the next interval uses consecutive stamps.
        self.previous_stamp = current
        self.sample_index += 1
        invalid = period is not None and period < 0
        if period is not None and not invalid:
            self._add_period(period)
        count_valid = len(self.periods)
        result = Sample(
            index=self.sample_index,
            count=count,
            stamp=f'{stamp.sec}.{stamp.nanosec:09d}',
            period=period,
            invalid_period=invalid,
            mean=self._mean if count_valid else None,
            median=self._median() if count_valid else None,
            stddev=sqrt(max(0.0, self._sum_squared_deviations / count_valid))
            if count_valid else None,
        )
        if period is not None and not invalid:
            self.history.append(result)
        return result
