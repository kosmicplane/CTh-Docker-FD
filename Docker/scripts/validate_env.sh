#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source /opt/venv/bin/activate
source /workspace/ros2_ws/install/setup.bash

export ACADOS_SOURCE_DIR=/opt/acados
export LD_LIBRARY_PATH=/opt/acados/lib:${LD_LIBRARY_PATH}
export PYTHONPATH=/opt/acados/interfaces/acados_template:${PYTHONPATH}

echo "Python:"
which python
python -c "import sys; print(sys.executable)"

echo ""
echo "ACADOS:"
python -c "import acados_template, casadi; from acados_template import AcadosModel; print('ACADOS OK')"

echo ""
echo "ROS Python dependencies:"
python -c "import rclpy; print('rclpy OK')"
python -c "import em; print('empy Interpreter:', hasattr(em, 'Interpreter'))"
python -c "import catkin_pkg; from lark import Lark; print('catkin_pkg + lark OK')"

echo ""
echo "ROS packages:"
ros2 pkg list | grep -E 'px4|mpc' || true
