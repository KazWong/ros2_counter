"""Publish a stamped unsigned counter at 10 Hz."""

import rclpy
from rclpy.node import Node
from ros2_counter_interfaces.msg import CounterStamped

from .model import next_count


class CounterPublisher(Node):
    def __init__(self):
        super().__init__('counter_publisher')
        self.count = 0
        self.publisher = self.create_publisher(CounterStamped, '/counter', 10)
        self.timer = self.create_timer(0.1, self.publish_count)

    def publish_count(self):
        message = CounterStamped()
        message.stamp = self.get_clock().now().to_msg()
        message.count = self.count
        self.publisher.publish(message)
        self.count = next_count(self.count)


def main(args=None):
    rclpy.init(args=args)
    node = CounterPublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
