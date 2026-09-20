#!/usr/bin/env bash
set -euo pipefail
python3 -m compileall -q src/ros2_counter/ros2_counter src/ros2_counter/test
PYTHONPATH=src/ros2_counter python3 -m pytest src/ros2_counter/test
if command -v ruff >/dev/null 2>&1; then
  ruff check src/ros2_counter
fi
