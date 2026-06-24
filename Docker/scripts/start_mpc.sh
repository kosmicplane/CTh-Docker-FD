#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source /opt/venv/bin/activate
source /workspace/ros2_ws/install/setup.bash

export ACADOS_SOURCE_DIR=/opt/acados
export LD_LIBRARY_PATH=/opt/acados/lib:${LD_LIBRARY_PATH}
export PYTHONPATH=/opt/acados/interfaces/acados_template:${PYTHONPATH}

python -c "import acados_template, casadi; from acados_template import AcadosModel; print('ACADOS OK before launch')"

echo "Starting MPC for spacecraft/Drone, ex: ros2 launch px4_mpc mpc_spacecraft_launch.py mode:=wrench setpoint_from_rviz:=False"
echo " ros2 launch px4_mpc mpc_quadrotor_launch.py 
