import importlib
import sys
from math import isclose, sqrt
from statistics import mean, median, pstdev
from types import ModuleType, SimpleNamespace

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


def test_sustained_stream_retains_cumulative_statistics():
    model = TimingModel()
    model.observe(0, SimpleNamespace(sec=0, nanosec=0))
    periods_ns = (90_000_000, 110_000_000, 100_000_000, 120_000_000)
    elapsed_ns = 0
    for index in range(1, 10_001):
        elapsed_ns += periods_ns[index % len(periods_ns)]
        sample = model.observe(
            index, SimpleNamespace(
                sec=elapsed_ns // 1_000_000_000,
                nanosec=elapsed_ns % 1_000_000_000,
            ),
        )
    assert len(model.history) == 10_000
    assert len(model.periods) == 10_000
    assert isclose(sample.mean, mean(model.periods), abs_tol=1e-12)
    assert isclose(sample.median, median(model.periods), abs_tol=1e-12)
    assert isclose(sample.stddev, pstdev(model.periods), abs_tol=1e-12)


def test_view_coalesces_sustained_updates_and_cancels_draw_on_close(monkeypatch):
    # Exercise the view's event scheduling without requiring a display or ROS.
    matplotlib = ModuleType('matplotlib')
    backends = ModuleType('matplotlib.backends')
    tkagg = ModuleType('matplotlib.backends.backend_tkagg')
    figure = ModuleType('matplotlib.figure')
    tkinter = ModuleType('tkinter')
    tkagg.FigureCanvasTkAgg = object
    figure.Figure = object
    rclpy = ModuleType('rclpy')
    executors = ModuleType('rclpy.executors')
    executors.ExternalShutdownException = type('ExternalShutdownException',
                                              (Exception,), {})
    for name, module in (
        ('matplotlib', matplotlib), ('matplotlib.backends', backends),
        ('matplotlib.backends.backend_tkagg', tkagg),
        ('matplotlib.figure', figure), ('tkinter', tkinter), ('rclpy', rclpy),
        ('rclpy.executors', executors),
    ):
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.delitem(sys.modules, 'ros2_counter.view', raising=False)
    try:
        view_module = importlib.import_module('ros2_counter.view')
        view = view_module.CounterView.__new__(view_module.CounterView)
        jobs = []
        canceled = []
        destroyed = []
        view.root = SimpleNamespace(
            after=lambda delay, callback: jobs.append((delay, callback)) or len(jobs),
            after_cancel=canceled.append,
            destroy=lambda: destroyed.append(True),
        )
        view.closed = False
        view._plot_job = None
        view._history = []
        view.count_label = SimpleNamespace(config=lambda **kwargs: None)
        view.stamp_label = SimpleNamespace(config=lambda **kwargs: None)
        view.lines = {
            name: SimpleNamespace(set_data=lambda x, y, name=name: plotted.__setitem__(
                name, (x, y)))
            for name in ('Mean', 'Median', 'Population SD')
        }
        view.axes = SimpleNamespace(relim=lambda: None,
                                    autoscale_view=lambda: None)
        draws = []
        view.canvas = SimpleNamespace(draw_idle=lambda: draws.append(True))
        plotted = {}
        history = []
        for index in range(1, 5001):
            sample = SimpleNamespace(index=index, count=index, stamp=str(index),
                                     mean=0.1, median=0.1, stddev=0.01)
            history.append(sample)
            view.update(sample, history)
        assert len(jobs) == 1
        view._draw_plot()
        assert len(draws) == 1
        assert all(len(x) == view_module.MAX_PLOT_POINTS
                   and x[-1] == 5000 for x, _ in plotted.values())
        view.update(sample, history)
        assert len(jobs) == 2
        view.close()
        assert canceled == [2]
        assert destroyed == [True]
    finally:
        sys.modules.pop('ros2_counter.view', None)


def test_subscriber_warns_and_excludes_negative_period(monkeypatch):
    # Import the subscriber without a ROS installation or interactive display.
    rclpy = ModuleType('rclpy')
    rclpy_node = ModuleType('rclpy.node')

    class FakeNode:
        def get_logger(self):
            return self.logger

    rclpy_node.Node = FakeNode
    interfaces = ModuleType('ros2_counter_interfaces')
    messages = ModuleType('ros2_counter_interfaces.msg')
    messages.CounterStamped = type('CounterStamped', (), {})
    monkeypatch.setitem(sys.modules, 'rclpy', rclpy)
    monkeypatch.setitem(sys.modules, 'rclpy.node', rclpy_node)
    monkeypatch.setitem(sys.modules, 'ros2_counter_interfaces', interfaces)
    monkeypatch.setitem(sys.modules, 'ros2_counter_interfaces.msg', messages)
    monkeypatch.delitem(sys.modules, 'ros2_counter.subscriber', raising=False)
    try:
        subscriber_module = importlib.import_module('ros2_counter.subscriber')
        subscriber = subscriber_module.CounterSubscriber.__new__(
            subscriber_module.CounterSubscriber
        )
        warnings = []
        subscriber.logger = SimpleNamespace(info=lambda message: None, warn=warnings.append)
        subscriber.model = TimingModel()
        subscriber.on_sample = None
        for count, time in enumerate((2.0, 1.9, 2.0)):
            subscriber.receive(SimpleNamespace(count=count, stamp=stamp(time)))
        assert warnings == ['Negative publisher timestamp interval excluded']
        assert len(subscriber.model.periods) == 1
        assert isclose(subscriber.model.periods[0], 0.1, abs_tol=1e-12)
    finally:
        sys.modules.pop('ros2_counter.subscriber', None)
