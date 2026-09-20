#!/usr/bin/env python3
"""ROS subscriber and Tk/matplotlib presentation for counter timing."""

from __future__ import annotations

from collections.abc import Callable

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from ros2_counter.msg import CounterStamped

from .timing import TimingSnapshot, TimingState


class CounterSubscriber(Node):
    def __init__(self, on_update: Callable[[TimingSnapshot], None] | None = None) -> None:
        super().__init__("counter_subscriber_gui")
        self._timing = TimingState()
        self._on_update = on_update
        self._subscription = self.create_subscription(
            CounterStamped, "/counter", self._on_message, 10
        )

    @property
    def snapshot(self) -> TimingSnapshot:
        return self._timing.snapshot()

    def _on_message(self, message: CounterStamped) -> None:
        snapshot, valid = self._timing.observe(message.count, message.stamp)
        timestamp = f"{message.stamp.sec}.{message.stamp.nanosec:09d}"
        if snapshot.latest_period is None:
            self.get_logger().info(f"count={message.count} publisher_stamp={timestamp}")
        else:
            self.get_logger().info(
                f"count={message.count} publisher_stamp={timestamp} "
                f"period={snapshot.latest_period:.9f}s"
            )
            if not valid:
                self.get_logger().warning(
                    f"negative publisher timestamp interval rejected: "
                    f"{snapshot.latest_period:.9f}s"
                )
        if self._on_update is not None:
            self._on_update(snapshot)


class CounterGui:
    """Tk view; all methods are called on Tk's event thread."""

    def __init__(self, root: object, node: CounterSubscriber) -> None:
        import tkinter as tk

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        self._root = root
        self._node = node
        self._closed = False
        self._after_id: str | None = None

        root.title("ROS 2 Counter Timing")
        self._count = tk.StringVar(value="Count: waiting")
        self._stamp = tk.StringVar(value="Publisher timestamp: waiting")
        tk.Label(root, textvariable=self._count).pack(anchor="w")
        tk.Label(root, textvariable=self._stamp).pack(anchor="w")

        figure = Figure(figsize=(7, 4), dpi=100)
        self._axes = figure.add_subplot(111)
        self._axes.set_xlabel("Valid interval index")
        self._axes.set_ylabel("Timing (seconds)")
        (self._mean_line,) = self._axes.plot([], [], label="Mean")
        (self._median_line,) = self._axes.plot([], [], label="Median")
        (self._sd_line,) = self._axes.plot([], [], label="Population standard deviation")
        self._axes.legend()
        self._canvas = FigureCanvasTkAgg(figure, master=root)
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        root.protocol("WM_DELETE_WINDOW", self.close)
        self._schedule_spin()

    def update(self, snapshot: TimingSnapshot) -> None:
        if self._closed:
            return
        self._count.set(f"Count: {snapshot.latest_count}")
        self._stamp.set(f"Publisher timestamp: {snapshot.latest_timestamp:.9f} s")
        x_values = snapshot.sample_indices
        self._mean_line.set_data(x_values, snapshot.means)
        self._median_line.set_data(x_values, snapshot.medians)
        self._sd_line.set_data(x_values, snapshot.standard_deviations)
        self._axes.relim()
        self._axes.autoscale_view()
        self._canvas.draw_idle()

    def _schedule_spin(self) -> None:
        if not self._closed:
            self._after_id = self._root.after(10, self._spin_once)

    def _spin_once(self) -> None:
        if self._closed:
            return
        if not rclpy.ok():
            self.close()
            return
        try:
            rclpy.spin_once(self._node, timeout_sec=0.0)
        except ExternalShutdownException:
            self.close()
            return
        self._schedule_spin()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._after_id is not None:
            self._root.after_cancel(self._after_id)
            self._after_id = None
        self._root.quit()
        self._root.destroy()


def main(args: list[str] | None = None) -> None:
    import tkinter as tk

    rclpy.init(args=args)
    node: CounterSubscriber | None = None
    gui: CounterGui | None = None
    try:
        root = tk.Tk()
        node = CounterSubscriber(on_update=lambda snapshot: gui.update(snapshot) if gui else None)
        gui = CounterGui(root, node)
        root.mainloop()
    except KeyboardInterrupt:
        if gui is not None:
            gui.close()
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
