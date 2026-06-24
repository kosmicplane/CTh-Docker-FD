#!/bin/bash
set -e

echo "Updating embedded source repositories..."

for repo in /workspace/ros2_ws/src/px4_msgs /workspace/ros2_ws/src/px4-offboard /workspace/ros2_ws/src/px4-mpc /workspace/PX4-Autopilot; do
    if [ -d "$repo/.git" ]; then
        echo "Updating $repo"
        git -C "$repo" pull --ff-only || true
        git -C "$repo" submodule update --init --recursive || true
    else
        echo "Skipping $repo; not a git repository."
    fi
done
