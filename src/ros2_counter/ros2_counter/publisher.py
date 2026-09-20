"""ROS 2 stamped uint32 counter publisher."""

from __future__ import annotations

import rclpy
from rclpy.node import Node

from ros2_counter.msg import CounterStamped

from .timing import CounterSequence

PUBLISH_PERIOD_SECONDS = 0.1


class CounterPublisher(Node):
    def __init__(self) -> None:
        super().__init__("counter_publisher")
        self._publisher = self.create_publisher(CounterStamped, "/counter", 10)
        self._counter = CounterSequence()
        self._timer = self.create_timer(PUBLISH_PERIOD_SECONDS, self._publish_next)

    def _publish_next(self) -> None:
        message = CounterStamped()
        message.stamp = self.get_clock().now().to_msg()
        message.count = self._counter.take()
        self._publisher.publish(message)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = CounterPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
