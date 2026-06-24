#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source /opt/venv/bin/activate

export ACADOS_SOURCE_DIR=/opt/acados
export LD_LIBRARY_PATH=/opt/acados/lib:${LD_LIBRARY_PATH}
export PYTHONPATH=/opt/acados/interfaces/acados_template:${PYTHONPATH}

if [ -f /workspace/ros2_ws/install/setup.bash ]; then
    source /workspace/ros2_ws/install/setup.bash
fi

exec "$@"
