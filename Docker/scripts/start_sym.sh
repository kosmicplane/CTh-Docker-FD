#!/usr/bin/env bash
set -e

SESSION="spacecraft_sim"

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -n main

# Pane 0: XRCE
tmux send-keys -t "$SESSION":0.0 \
"source /opt/ros/jazzy/setup.bash && source /workspace/ros2_ws/install/setup.bash && /workspace/scripts/start_xrce.sh" C-m

# Split vertical: PX4
tmux split-window -h -t "$SESSION":0.0
tmux send-keys -t "$SESSION":0.1 \
"cd /workspace/PX4-Autopilot && make px4_sitl_spacecraft gz_atmos" C-m

# Split bottom-left: MPC
tmux split-window -v -t "$SESSION":0.0
tmux send-keys -t "$SESSION":0.2 \
"source /opt/ros/jazzy/setup.bash && source /opt/venv/bin/activate && cd /workspace/ros2_ws && colcon build --symlink-install --packages-select px4_mpc && source install/setup.bash && ros2 launch px4_mpc mpc_spacecraft_launch.py mode:=wrench setpoint_from_rviz:=False" C-m

# Split bottom-right: Monitor
tmux split-window -v -t "$SESSION":0.1
tmux send-keys -t "$SESSION":0.3 \
"source /opt/ros/jazzy/setup.bash && source /workspace/ros2_ws/install/setup.bash && echo 'Waiting 15s for PX4/MPC...' && sleep 15 && ros2 topic list | sort | grep fmu && echo '--- Outputs ---' && timeout 5 ros2 topic hz /fmu/in/offboard_control_mode && timeout 5 ros2 topic hz /fmu/in/vehicle_thrust_setpoint && timeout 5 ros2 topic hz /fmu/in/vehicle_torque_setpoint" C-m

tmux select-layout -t "$SESSION":0 tiled
tmux attach -t "$SESSION"