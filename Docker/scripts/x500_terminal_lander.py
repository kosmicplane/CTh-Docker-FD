
#!/usr/bin/env python3

import math
import threading
import time
from dataclasses import dataclass
from typing import List, Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy, QoSHistoryPolicy

from px4_msgs.msg import OffboardControlMode
from px4_msgs.msg import TrajectorySetpoint
from px4_msgs.msg import VehicleCommand


@dataclass
class Waypoint:
    x: float
    y: float
    altitude: float   # positive UP in meters, user-friendly
    yaw_deg: float
    duration: float   # seconds


class X500TerminalLander(Node):
    def __init__(self):
        super().__init__('x500_terminal_lander')

        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.offboard_pub = self.create_publisher(
            OffboardControlMode,
            '/fmu/in/offboard_control_mode',
            qos,
        )

        self.trajectory_pub = self.create_publisher(
            TrajectorySetpoint,
            '/fmu/in/trajectory_setpoint',
            qos,
        )

        self.command_pub = self.create_publisher(
            VehicleCommand,
            '/fmu/in/vehicle_command',
            qos,
        )

        self.sequence: List[Waypoint] = []
        self.active = False
        self.current_index = 0
        self.segment_start_time = time.time()

        # Punto inicial seguro: despegar/hold a 2 m
        self.current_wp = Waypoint(0.0, 0.0, 2.0, 0.0, 3.0)

        self.offboard_counter = 0
        self.commanded_offboard = False
        self.commanded_arm = False

        self.timer = self.create_timer(0.05, self.timer_callback)  # 20 Hz

        self.get_logger().info("X500 terminal lander started.")
        self.print_help()

        input_thread = threading.Thread(target=self.terminal_loop, daemon=True)
        input_thread.start()

    def now_us(self) -> int:
        return int(self.get_clock().now().nanoseconds / 1000)

    def publish_offboard_heartbeat(self):
        msg = OffboardControlMode()
        msg.timestamp = self.now_us()
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.thrust_and_torque = False
        msg.direct_actuator = False
        self.offboard_pub.publish(msg)

    def publish_trajectory_setpoint(self, wp: Waypoint):
        """
        PX4 uses NED:
          x forward
          y right
          z down

        User enters altitude positive UP.
        Therefore:
          PX4 z = -altitude
        """
        msg = TrajectorySetpoint()
        msg.timestamp = self.now_us()
        msg.position = [float(wp.x), float(wp.y), float(-wp.altitude)]
        msg.velocity = [float('nan'), float('nan'), float('nan')]
        msg.acceleration = [float('nan'), float('nan'), float('nan')]
        msg.jerk = [float('nan'), float('nan'), float('nan')]
        msg.yaw = math.radians(wp.yaw_deg)
        msg.yawspeed = float('nan')
        self.trajectory_pub.publish(msg)

    def publish_vehicle_command(self, command, param1=0.0, param2=0.0, param3=0.0):
        msg = VehicleCommand()
        msg.timestamp = self.now_us()
        msg.param1 = float(param1)
        msg.param2 = float(param2)
        msg.param3 = float(param3)
        msg.param4 = 0.0
        msg.param5 = 0.0
        msg.param6 = 0.0
        msg.param7 = 0.0
        msg.command = command
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        self.command_pub.publish(msg)

    def arm(self):
        self.get_logger().info("Sending ARM command.")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
            param1=1.0,
        )

    def disarm(self):
        self.get_logger().info("Sending DISARM command.")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
            param1=0.0,
        )

    def set_offboard_mode(self):
        self.get_logger().info("Sending OFFBOARD mode command.")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1=1.0,
            param2=6.0,
        )

    def land_px4(self):
        self.get_logger().info("Sending PX4 NAV_LAND command.")
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_NAV_LAND,
            param1=0.0,
        )

    def timer_callback(self):
        self.publish_offboard_heartbeat()

        # PX4 requiere setpoints antes de entrar a OFFBOARD.
        self.publish_trajectory_setpoint(self.current_wp)

        self.offboard_counter += 1

        # Después de ~1 segundo de setpoints, mandar offboard + arm.
        if self.active and self.offboard_counter > 20:
            if not self.commanded_offboard:
                self.set_offboard_mode()
                self.commanded_offboard = True

            if not self.commanded_arm:
                self.arm()
                self.commanded_arm = True

        if not self.active:
            return

        if not self.sequence:
            return

        elapsed = time.time() - self.segment_start_time
        current_target = self.sequence[self.current_index]
        self.current_wp = current_target

        if elapsed >= current_target.duration:
            self.current_index += 1
            self.segment_start_time = time.time()

            if self.current_index >= len(self.sequence):
                self.get_logger().info("Sequence finished. Sending LAND command.")
                self.active = False
                self.current_index = 0
                self.land_px4()

    def start_sequence(self, seq: List[Waypoint]):
        if not seq:
            self.get_logger().warn("Empty sequence. Nothing to run.")
            return

        self.sequence = seq
        self.current_index = 0
        self.segment_start_time = time.time()
        self.active = True
        self.commanded_offboard = False
        self.commanded_arm = False
        self.offboard_counter = 0
        self.current_wp = seq[0]

        self.get_logger().info(f"Started sequence with {len(seq)} waypoints.")

    def print_help(self):
        print("")
        print("Commands:")
        print("  demo")
        print("      Runs demo path and then lands.")
        print("")
        print("  point x y altitude yaw_deg duration")
        print("      Sends one point. Example:")
        print("      point 1.0 0.0 2.0 0.0 5.0")
        print("")
        print("  land")
        print("      Sends PX4 LAND command.")
        print("")
        print("  arm")
        print("      Arms vehicle.")
        print("")
        print("  offboard")
        print("      Sets OFFBOARD mode.")
        print("")
        print("  disarm")
        print("      Disarms vehicle.")
        print("")
        print("  hold x y altitude yaw_deg")
        print("      Holds a point continuously.")
        print("")
        print("  quit")
        print("      Exit.")
        print("")

    def terminal_loop(self):
        while rclpy.ok():
            try:
                cmd = input("x500> ").strip()
            except EOFError:
                return

            if not cmd:
                continue

            parts = cmd.split()
            name = parts[0].lower()

            try:
                if name == "help":
                    self.print_help()

                elif name == "demo":
                    seq = [
                        Waypoint(0.0, 0.0, 2.0, 0.0, 5.0),
                        Waypoint(2.0, 0.0, 2.0, 0.0, 5.0),
                        Waypoint(2.0, 1.0, 1.5, 45.0, 5.0),
                        Waypoint(1.0, 1.0, 1.0, 90.0, 5.0),
                        Waypoint(0.0, 0.0, 0.4, 0.0, 5.0),
                    ]
                    self.start_sequence(seq)

                elif name == "point":
                    if len(parts) != 6:
                        print("Usage: point x y altitude yaw_deg duration")
                        continue

                    x = float(parts[1])
                    y = float(parts[2])
                    alt = float(parts[3])
                    yaw = float(parts[4])
                    duration = float(parts[5])

                    self.start_sequence([
                        Waypoint(x, y, alt, yaw, duration)
                    ])

                elif name == "hold":
                    if len(parts) != 5:
                        print("Usage: hold x y altitude yaw_deg")
                        continue

                    x = float(parts[1])
                    y = float(parts[2])
                    alt = float(parts[3])
                    yaw = float(parts[4])

                    self.active = False
                    self.current_wp = Waypoint(x, y, alt, yaw, 1.0)
                    print(f"Holding x={x}, y={y}, altitude={alt}, yaw={yaw}")

                elif name == "land":
                    self.land_px4()

                elif name == "arm":
                    self.arm()

                elif name == "offboard":
                    self.set_offboard_mode()

                elif name == "disarm":
                    self.disarm()

                elif name == "quit":
                    print("Exiting...")
                    rclpy.shutdown()
                    return

                else:
                    print("Unknown command. Type: help")

            except Exception as e:
                print(f"Error: {e}")


def main():
    rclpy.init()
    node = X500TerminalLander()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()