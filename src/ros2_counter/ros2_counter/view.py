"""Tk event loop owns both drawing and nonblocking ROS callback execution."""

import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import rclpy
from rclpy.executors import ExternalShutdownException

MAX_PLOT_POINTS = 500
PLOT_INTERVAL_MS = 100


class CounterView:
    def __init__(self, node):
        self.node = node
        self.closed = False
        self._history = []
        self._plot_job = None
        self.root = tk.Tk()
        self.root.title('ROS counter')
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.count_label = tk.Label(self.root, text='Count: waiting')
        self.count_label.pack()
        self.stamp_label = tk.Label(self.root, text='Publisher time: waiting')
        self.stamp_label.pack()
        figure = Figure(figsize=(8, 4))
        self.axes = figure.add_subplot(111)
        self.axes.set_xlabel('Received sample index')
        self.axes.set_ylabel('Period statistics (s)')
        self.lines = {
            name: self.axes.plot([], [], label=name)[0]
            for name in ('Mean', 'Median', 'Population SD')
        }
        self.axes.legend()
        self.canvas = FigureCanvasTkAgg(figure, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.root.after(10, self.poll_ros)

    def update(self, sample, history):
        self.count_label.config(text=f'Count: {sample.count}')
        self.stamp_label.config(text=f'Publisher time: {sample.stamp}')
        self._history = history
        if self._plot_job is None:
            self._plot_job = self.root.after(PLOT_INTERVAL_MS, self._draw_plot)

    def _draw_plot(self):
        self._plot_job = None
        if self.closed:
            return
        # The model retains every interval; only a bounded recent window is
        # passed to Matplotlib so the GUI event loop has bounded drawing work.
        visible = self._history[-MAX_PLOT_POINTS:]
        x = [item.index for item in visible]
        for name, field in (
            ('Mean', 'mean'), ('Median', 'median'), ('Population SD', 'stddev')
        ):
            self.lines[name].set_data(x, [getattr(item, field) for item in visible])
        self.axes.relim()
        self.axes.autoscale_view()
        self.canvas.draw_idle()

    def poll_ros(self):
        if self.closed:
            return
        if not rclpy.ok():
            self.close()
            return
        try:
            rclpy.spin_once(self.node, timeout_sec=0)
        except ExternalShutdownException:
            self.close()
            return
        if not self.closed:
            self.root.after(10, self.poll_ros)

    def run(self):
        self.root.mainloop()

    def close(self):
        if not self.closed:
            self.closed = True
            if self._plot_job is not None:
                self.root.after_cancel(self._plot_job)
                self._plot_job = None
            self.root.destroy()
