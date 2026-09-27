"""Optional display-backed smoke test for the Tk plotting view."""

import os
from types import SimpleNamespace

import pytest

from ros2_counter.model import TimingModel


@pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='No display available')
def test_gui_updates_and_closes():
    from ros2_counter.view import CounterView

    view = CounterView(SimpleNamespace())
    try:
        model = TimingModel()
        model.observe(0, SimpleNamespace(sec=1, nanosec=0))
        sample = model.observe(1, SimpleNamespace(sec=1, nanosec=100000000))
        view.update(sample, model.history)
        view.root.update_idletasks()
        assert view.count_label.cget('text') == 'Count: 1'
        assert '1.100000000' in view.stamp_label.cget('text')
        assert all(len(line.get_xdata()) == 1 for line in view.lines.values())
    finally:
        view.close()
    assert view.closed
