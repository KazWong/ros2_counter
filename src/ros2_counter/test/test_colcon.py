"""Run the ROS and GUI pytest checks through setuptools test discovery."""

from pathlib import Path
import unittest

import pytest


class ColconTests(unittest.TestCase):
    def test_ros_and_gui(self):
        test_dir = Path(__file__).parent
        result = pytest.main([
            '-q',
            str(test_dir / 'test_ros_integration.py'),
            str(test_dir / 'test_gui_smoke.py'),
        ])
        self.assertEqual(result, 0)
