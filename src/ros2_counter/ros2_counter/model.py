"""Widget-independent counter and publisher-time statistics."""

from dataclasses import dataclass
from statistics import mean, median, pstdev

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
            self.periods.append(period)
        result = Sample(
            index=self.sample_index,
            count=count,
            stamp=f'{stamp.sec}.{stamp.nanosec:09d}',
            period=period,
            invalid_period=invalid,
            mean=mean(self.periods) if self.periods else None,
            median=median(self.periods) if self.periods else None,
            stddev=pstdev(self.periods) if self.periods else None,
        )
        if period is not None and not invalid:
            self.history.append(result)
        return result
