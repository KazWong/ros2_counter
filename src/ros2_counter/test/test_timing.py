#!/usr/bin/env python3
from dataclasses import dataclass

import pytest
from ros2_counter.timing import CounterSequence, TimingState, interval_seconds, stamp_to_seconds


@dataclass
class Stamp:
    sec: int
    nanosec: int


def test_counter_begins_at_zero_and_increments() -> None:
    counter = CounterSequence()
    assert [counter.take(), counter.take()] == [0, 1]


def test_counter_wraps_at_uint32_maximum() -> None:
    counter = CounterSequence(4_294_967_295)
    assert [counter.take(), counter.take()] == [4_294_967_295, 0]


def test_timestamp_conversion_and_consecutive_interval() -> None:
    previous = Stamp(10, 950_000_000)
    current = Stamp(11, 50_000_000)
    assert stamp_to_seconds(previous) == pytest.approx(10.95)
    assert interval_seconds(current, previous) == pytest.approx(0.1)


def test_cumulative_statistics_match_reference_values() -> None:
    state = TimingState()
    state.observe(0, Stamp(1, 0))
    state.observe(1, Stamp(1, 100_000_000))
    state.observe(2, Stamp(1, 210_000_000))
    snapshot, valid = state.observe(3, Stamp(1, 300_000_000))

    assert valid
    assert snapshot.intervals == pytest.approx((0.10, 0.11, 0.09))
    assert snapshot.means[-1] == pytest.approx(0.10)
    assert snapshot.medians[-1] == pytest.approx(0.10)
    assert snapshot.standard_deviations[-1] == pytest.approx(0.0081649658)
    assert snapshot.sample_indices == (1, 2, 3)


def test_negative_interval_is_rejected_and_next_interval_is_consecutive() -> None:
    state = TimingState()
    state.observe(0, Stamp(2, 0))
    rejected, valid = state.observe(1, Stamp(1, 900_000_000))
    recovered, recovered_valid = state.observe(2, Stamp(2, 0))

    assert not valid
    assert rejected.latest_period == pytest.approx(-0.1)
    assert rejected.intervals == ()
    assert recovered_valid
    assert recovered.intervals == pytest.approx((0.1,))
