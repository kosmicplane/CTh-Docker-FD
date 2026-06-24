# ATMOS Docker Embedded Workspace

This version embeds the ROS 2 workspace inside the Docker image.

It includes:

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo Harmonic
- PX4-Autopilot
- Micro XRCE-DDS Agent
- RViz2
- ACADOS
- acados_template
- CasADi
- px4_msgs
- px4-offboard
- px4-mpc

No Isaac Sim. No Omniverse.

## Key difference

This version does **not** mount `../ros2_ws` as a Docker volume.

The Dockerfile clones and builds:

```text
/workspace/ros2_ws/src/px4_msgs
/workspace/ros2_ws/src/px4-offboard
/workspace/ros2_ws/src/px4-mpc
```

during `docker compose build`.

This makes the image more reproducible.

## Build

```bash
cd ~/ATMOS/Docker
docker compose build --no-cache
```

## Allow GUI

```bash
xhost +local:docker
```

## Start container

```bash
docker compose up -d
docker exec -it atmos_jazzy bash
```

## Validate

Inside the container:

```bash
/workspace/scripts/validate_env.sh
```

## Rebuild workspace inside container, if needed

```bash
/workspace/scripts/build_ros_ws.sh
```

## Launch flow

Use separate host terminals.

### Terminal 1: XRCE Agent

```bash
docker exec -it atmos_jazzy bash
/workspace/scripts/start_xrce.sh
```

### Terminal 2: PX4 SITL + Gazebo Harmonic

```bash
docker exec -it atmos_jazzy bash
/workspace/scripts/start_px4.sh
```

### Terminal 3: MPC

```bash
docker exec -it atmos_jazzy bash
/workspace/scripts/start_mpc.sh
```

### Terminal 4: RViz2

```bash
docker exec -it atmos_jazzy bash
/workspace/scripts/start_rviz.sh
```

## Updating source repos inside the image/container

Inside the container:

```bash
/workspace/scripts/update_repos.sh
/workspace/scripts/build_ros_ws.sh
```

For permanent updates, rebuild the image.
