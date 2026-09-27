"""Run through colcon test in the ros2-humble lane."""

import time

import rclpy
from rclpy.executors import SingleThreadedExecutor

from ros2_counter.publisher import CounterPublisher
from ros2_counter.subscriber import CounterSubscriber
from ros2_counter_interfaces.msg import CounterStamped


def test_ros_counter_delivery_and_cadence(capfd):
    rclpy.init()
    publisher = CounterPublisher()
    assert publisher.timer.timer_period_ns == 100_000_000
    assert publisher.publisher.topic_name == '/counter'
    assert CounterStamped.get_fields_and_field_types() == {
        'stamp': 'builtin_interfaces/Time', 'count': 'uint32'
    }
    samples = []
    subscriber = CounterSubscriber(lambda sample, history: samples.append(sample))
    executor = SingleThreadedExecutor()
    executor.add_node(publisher)
    executor.add_node(subscriber)
    try:
        deadline = time.monotonic() + 5
        while len(samples) < 7 and time.monotonic() < deadline:
            executor.spin_once(timeout_sec=0.1)
        assert len(samples) >= 7, 'Publisher/subscriber discovery or delivery failed'
        assert samples[0].count == 0
        assert all(b.count == a.count + 1 for a, b in zip(samples, samples[1:]))
        assert all(0 <= sample.count <= 4294967295 for sample in samples)
        assert all(sample.stamp != '0.000000000' for sample in samples)
        periods = [sample.period for sample in samples[1:]]
        assert all(period is not None and period >= 0 for period in periods)
        # Loaded CI hosts may jitter; the average must still be near 0.1 s.
        assert 0.07 <= sum(periods) / len(periods) <= 0.13
        assert len(subscriber.model.history) == len(periods)
        output = capfd.readouterr()
        console = output.out + output.err
        assert f'count={samples[0].count} stamp={samples[0].stamp}' in console
        assert 'period=' in console
    finally:
        executor.remove_node(subscriber)
        executor.remove_node(publisher)
        executor.shutdown()
        subscriber.destroy_node()
        publisher.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
