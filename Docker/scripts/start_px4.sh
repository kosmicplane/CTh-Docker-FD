#!/bin/bash
set -e

cd /workspace/PX4-Autopilot
git submodule update --init --recursive
echo "Build PX4 SITL for spacecraft/Drone, ex: make px4_sitl_spacecraft gz_atmos or make px4_sitl gz_x500"
