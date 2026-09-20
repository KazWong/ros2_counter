#!/usr/bin/env python3
from __future__ import annotations

import os
import time
from itertools import pairwise
from unittest.mock import Mock, patch

import pytest

rclpy = pytest.importorskip("rclpy", reason="ROS 2 environment is not sourced")
pytest.importorskip("ros2_counter.msg", reason="generated message is not built")

from rclpy.executors import SingleThreadedExecutor
from ros2_counter.publisher import CounterPublisher
from ros2_counter.subscriber import CounterSubscriber

from ros2_counter.msg import CounterStamped

pytestmark = pytest.mark.ros


@pytest.fixture
def ros_context():
    rclpy.init()
    try:
        yield
    finally:
        if rclpy.ok():
            rclpy.shutdown()


def test_real_nodes_discover_and_publish_regular_stamped_sequence(ros_context) -> None:
    snapshots = []
    publisher = CounterPublisher()
    subscriber = CounterSubscriber(on_update=snapshots.append)
    executor = SingleThreadedExecutor()
    executor.add_node(publisher)
    executor.add_node(subscriber)
    deadline = time.monotonic() + 5.0
    try:
        while len(snapshots) < 6 and time.monotonic() < deadline:
            executor.spin_once(timeout_sec=0.05)
    finally:
        executor.remove_node(subscriber)
        executor.remove_node(publisher)
        subscriber.destroy_node()
        publisher.destroy_node()
        executor.shutdown()

    assert len(snapshots) >= 6
    counts = [snapshot.latest_count for snapshot in snapshots]
    assert all(count is not None and 0 <= count <= 4_294_967_295 for count in counts)
    assert all(current == (previous + 1) % (1 << 32) for previous, current in pairwise(counts))
    assert all(snapshot.latest_timestamp not in (None, 0.0) for snapshot in snapshots)
    intervals = snapshots[-1].intervals
    assert len(intervals) >= 5
    assert sorted(intervals)[len(intervals) // 2] == pytest.approx(0.1, abs=0.03)


def test_subscriber_console_output_includes_required_fields(ros_context) -> None:
    subscriber = CounterSubscriber()
    logger = Mock()
    try:
        with patch.object(subscriber, "get_logger", return_value=logger):
            first = CounterStamped()
            first.count = 7
            first.stamp.sec = 1
            subscriber._on_message(first)
            second = CounterStamped()
            second.count = 8
            second.stamp.sec = 1
            second.stamp.nanosec = 100_000_000
            subscriber._on_message(second)
            regressed = CounterStamped()
            regressed.count = 9
            regressed.stamp.sec = 1
            regressed.stamp.nanosec = 50_000_000
            subscriber._on_message(regressed)
    finally:
        subscriber.destroy_node()

    first_log = logger.info.call_args_list[0].args[0]
    second_log = logger.info.call_args_list[1].args[0]
    assert "count=7" in first_log and "publisher_stamp=1.000000000" in first_log
    assert "count=8" in second_log and "period=0.100000000s" in second_log
    assert "negative publisher timestamp interval rejected" in logger.warning.call_args.args[0]


@pytest.mark.gui
def test_gui_smoke_when_display_available(ros_context) -> None:
    if not os.environ.get("DISPLAY"):
        pytest.skip("DISPLAY is unavailable; headless timing/model tests remain active")

    import tkinter as tk

    from ros2_counter.subscriber import CounterGui

    root = tk.Tk()
    node = CounterSubscriber()
    gui = CounterGui(root, node)
    try:
        first = CounterStamped()
        first.stamp.sec = 1
        node._on_message(first)
        second = CounterStamped()
        second.count = 1
        second.stamp.sec = 1
        second.stamp.nanosec = 100_000_000
        node._on_message(second)
        gui.update(node.snapshot)
        root.update_idletasks()
        assert len(gui._mean_line.get_ydata()) == 1
        assert len(gui._median_line.get_ydata()) == 1
        assert len(gui._sd_line.get_ydata()) == 1
    finally:
        gui.close()
        node.destroy_node()
