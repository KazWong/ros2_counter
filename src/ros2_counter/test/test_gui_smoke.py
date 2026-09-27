"""Optional display-backed smoke test for the Tk plotting view."""

import os
from types import SimpleNamespace

import pytest

from ros2_counter.model import TimingModel


@pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='No display available')
def test_gui_updates_and_closes():
    from ros2_counter.view import CounterView, MAX_PLOT_POINTS

    view = CounterView(SimpleNamespace())
    try:
        model = TimingModel()
        model.observe(0, SimpleNamespace(sec=1, nanosec=0))
        sample = model.observe(1, SimpleNamespace(sec=1, nanosec=100000000))
        view.update(sample, model.history)
        view._draw_plot()
        view.root.update_idletasks()
        assert view.count_label.cget('text') == 'Count: 1'
        assert '1.100000000' in view.stamp_label.cget('text')
        assert all(len(line.get_xdata()) == 1 for line in view.lines.values())

        # A long stream must retain complete statistics while plotting only
        # a bounded window, and a pending draw must not prevent closing.
        for index in range(2, 5002):
            nanoseconds = 1_000_000_000 + index * 100_000_000
            sample = model.observe(index, SimpleNamespace(
                sec=nanoseconds // 1_000_000_000,
                nanosec=nanoseconds % 1_000_000_000,
            ))
            view.update(sample, model.history)
        view._draw_plot()
        assert len(model.history) == 5001
        assert all(len(line.get_xdata()) == MAX_PLOT_POINTS
                   for line in view.lines.values())
        assert all(line.get_xdata()[-1] == sample.index
                   for line in view.lines.values())
    finally:
        view.close()
    assert view.closed
