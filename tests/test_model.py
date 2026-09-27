from math import isclose, sqrt
from types import SimpleNamespace

from ros2_counter.model import TimingModel, next_count, stamp_seconds


def stamp(seconds):
    whole = int(seconds)
    return SimpleNamespace(sec=whole, nanosec=round((seconds - whole) * 1e9))


def test_counter_wrap_and_first_value():
    count = 0
    assert count == 0
    assert next_count(count) == 1
    assert next_count(4294967295) == 0


def test_timestamp_and_cumulative_statistics():
    assert stamp_seconds(SimpleNamespace(sec=2, nanosec=250000000)) == 2.25
    model = TimingModel()
    assert model.observe(0, stamp(10)).period is None
    for index, time in enumerate((10.10, 10.21, 10.30), start=1):
        result = model.observe(index, stamp(time))
    assert result.index == 4
    assert result.stamp == '10.300000000'
    assert isclose(result.mean, 0.1, abs_tol=1e-12)
    assert isclose(result.median, 0.1, abs_tol=1e-12)
    assert isclose(result.stddev, sqrt(0.0002 / 3), abs_tol=1e-12)
    assert len(model.history) == 3
    assert [sample.index for sample in model.history] == [2, 3, 4]


def test_negative_period_excluded_and_previous_stamp_advanced():
    model = TimingModel()
    model.observe(0, stamp(2.0))
    invalid = model.observe(1, stamp(1.9))
    assert invalid.period < 0
    assert invalid.invalid_period
    assert invalid.mean is None
    assert model.periods == []
    valid = model.observe(2, stamp(2.0))
    assert isclose(valid.period, 0.1, abs_tol=1e-12)
    assert isclose(valid.mean, 0.1, abs_tol=1e-12)
