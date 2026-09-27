"""Console subscriber with a responsive desktop statistics view."""

import rclpy
from rclpy.node import Node
from ros2_counter_interfaces.msg import CounterStamped

from .model import TimingModel


class CounterSubscriber(Node):
    def __init__(self, on_sample=None):
        super().__init__('counter_subscriber_gui')
        self.model = TimingModel()
        self.on_sample = on_sample
        self.subscription = self.create_subscription(
            CounterStamped, '/counter', self.receive, 10
        )

    def receive(self, message):
        sample = self.model.observe(message.count, message.stamp)
        suffix = '' if sample.period is None else f' period={sample.period:.9f} s'
        self.get_logger().info(
            f'count={sample.count} stamp={sample.stamp}{suffix}'
        )
        if sample.invalid_period:
            self.get_logger().warn('Negative publisher timestamp interval excluded')
        if self.on_sample is not None:
            self.on_sample(sample, self.model.history)


def main(args=None):
    # Tk and Matplotlib are loaded only for the interactive entry point.
    from .view import CounterView

    rclpy.init(args=args)
    node = CounterSubscriber()
    view = None
    try:
        view = CounterView(node)
        node.on_sample = view.update
        view.run()
    except KeyboardInterrupt:
        pass
    finally:
        if view is not None:
            view.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
