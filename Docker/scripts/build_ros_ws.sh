#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source /opt/venv/bin/activate

export ACADOS_SOURCE_DIR=/opt/acados
export LD_LIBRARY_PATH=/opt/acados/lib:${LD_LIBRARY_PATH}
export PYTHONPATH=/opt/acados/interfaces/acados_template:${PYTHONPATH}

cd /workspace/ros2_ws

echo "Rebuilding embedded ROS 2 workspace..."
colcon build --symlink-install

source install/setup.bash

echo ""
echo "Build finished. Detected PX4/MPC packages:"
ros2 pkg list | grep -E 'px4|mpc' || true
