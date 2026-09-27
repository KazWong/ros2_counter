#!/usr/bin/env bash
set -euo pipefail
# Headless checks; the framework runs ROS build/integration in ros2-humble.
python3 -m compileall -q src/ros2_counter/ros2_counter
PYTHONPATH="src/ros2_counter${PYTHONPATH:+:$PYTHONPATH}" python3 -m pytest -q tests/test_model.py
