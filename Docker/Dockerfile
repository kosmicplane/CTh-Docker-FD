FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Chicago
ENV ROS_DISTRO=jazzy
ENV ACADOS_SOURCE_DIR=/opt/acados
ENV LD_LIBRARY_PATH=/opt/acados/lib:${LD_LIBRARY_PATH}
ENV PYTHONPATH=/opt/acados/interfaces/acados_template:${PYTHONPATH}
ENV PATH=/opt/venv/bin:${PATH}
ENV QT_X11_NO_MITSHM=1

SHELL ["/bin/bash", "-c"]

# ----------------------------------------------------------------------------
# Base Ubuntu packages
# ----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales tzdata ca-certificates \
    curl wget git gnupg lsb-release software-properties-common \
    build-essential cmake ninja-build pkg-config make gcc g++ gfortran \
    ccache gdb nano vim htop less tree \
    python3 python3-pip python3-venv python3-dev \
    python3-setuptools python3-wheel \
    libeigen3-dev libyaml-cpp-dev libtinyxml2-dev libxml2-dev \
    libblas-dev liblapack-dev \
    libgl1-mesa-dev libglu1-mesa-dev libglx-mesa0 libegl1-mesa-dev mesa-utils \
    libopencv-dev libprotobuf-dev protobuf-compiler \
    libssl-dev libcurl4-openssl-dev \
    tmux\
    exiftool genromfs default-jre \
    gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl \
    libfuse2 libxcb-xinerama0 libxkbcommon-x11-0 libxcb-cursor-dev \
    net-tools iputils-ping iproute2 usbutils udev \
    && locale-gen en_US en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends \
    cppzmq-dev \
    libzmq3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# ----------------------------------------------------------------------------
# ROS 2 Jazzy
# ----------------------------------------------------------------------------
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg

RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu noble main" \
    > /etc/apt/sources.list.d/ros2.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-desktop \
    ros-dev-tools \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------------------------------
# Gazebo Harmonic
# ----------------------------------------------------------------------------
RUN curl https://packages.osrfoundation.org/gazebo.gpg \
    --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg

RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable noble main" \
    > /etc/apt/sources.list.d/gazebo-stable.list
RUN apt-get update && apt-get install -y --no-install-recommends \
    gz-harmonic \
    libgz-cmake3-dev \
    libgz-transport13-dev \
    && rm -rf /var/lib/apt/lists/*
# ----------------------------------------------------------------------------
# Python environment shared by ROS tools and ACADOS
# ----------------------------------------------------------------------------
RUN python3 -m venv /opt/venv

RUN pip install --upgrade pip setuptools wheel

RUN pip uninstall -y em || true && \
    pip install \
    colcon-common-extensions \
    vcstool \
    rosdep \
    casadi \
    numpy \
    scipy \
    matplotlib \
    cython \
    empy==3.3.4 \
    catkin_pkg \
    lark \
    packaging \
    pyyaml \
    netifaces \
    future \
    jinja2 \
    toml \
    jsonschema \
    pyserial \
    kconfiglib

# ----------------------------------------------------------------------------
# Micro XRCE-DDS Agent
# ----------------------------------------------------------------------------
RUN git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git /opt/MicroXRCE && \
    cd /opt/MicroXRCE && \
    mkdir -p build && cd build && \
    cmake .. && \
    make -j"$(nproc)" && \
    make install && \
    ldconfig

# ----------------------------------------------------------------------------
# ACADOS
# ----------------------------------------------------------------------------
RUN git clone https://github.com/acados/acados.git /opt/acados && \
    cd /opt/acados && \
    git submodule update --recursive --init

RUN mkdir -p /opt/acados/build && \
    cd /opt/acados/build && \
    cmake -DACADOS_WITH_QPOASES=ON .. && \
    make install -j"$(nproc)" && \
    ldconfig

RUN pip install -e /opt/acados/interfaces/acados_template

# ----------------------------------------------------------------------------
# ROS workspace embedded inside the image
# ----------------------------------------------------------------------------
RUN mkdir -p /workspace/ros2_ws/src

RUN git clone https://github.com/PX4/px4_msgs.git /workspace/ros2_ws/src/px4_msgs && \
    git clone https://github.com/Jaeyoung-Lim/px4-offboard.git /workspace/ros2_ws/src/px4-offboard && \
    git clone https://github.com/DISCOWER/px4-mpc.git /workspace/ros2_ws/src/px4-mpc

# Build ROS workspace during image build.
# This is the key change: px4_mpc is now inside the container, not mounted.
RUN source /opt/ros/jazzy/setup.bash && \
    source /opt/venv/bin/activate && \
    cd /workspace/ros2_ws && \
    colcon build --symlink-install

# ----------------------------------------------------------------------------
# PX4-Autopilot embedded inside the image
# ----------------------------------------------------------------------------
RUN git clone https://github.com/PX4/PX4-Autopilot.git --recursive /workspace/PX4-Autopilot
RUN cd /workspace/PX4-Autopilot && \
    bash ./Tools/setup/ubuntu.sh --no-nuttx --no-sim-tools || true
COPY Files/dds_topics.yaml /tmp/dds_topics.yaml

RUN cp /tmp/dds_topics.yaml \
    /workspace/PX4-Autopilot/src/modules/uxrce_dds_client/dds_topics.yaml
# ----------------------------------------------------------------------------
# rosdep
# ----------------------------------------------------------------------------
RUN rosdep init || true
RUN rosdep update || true

WORKDIR /workspace

# ----------------------------------------------------------------------------
# Helper scripts
# ----------------------------------------------------------------------------
COPY scripts/ /workspace/scripts/
RUN chmod +x /workspace/scripts/*.sh

# ----------------------------------------------------------------------------
# Build-time validation: fail early if Python/ROS/acados/workspace are inconsistent
# ----------------------------------------------------------------------------
RUN source /opt/ros/jazzy/setup.bash && \
    source /opt/venv/bin/activate && \
    source /workspace/ros2_ws/install/setup.bash && \
    python -c "import sys; print(sys.executable)" && \
    python -c "import rclpy; import casadi; import acados_template; from acados_template import AcadosModel; import em; import catkin_pkg; from lark import Lark; print('ROS + ACADOS Python validation OK')" && \
    ros2 pkg list | grep px4_mpc

RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "source /opt/venv/bin/activate" >> /root/.bashrc && \
    echo "source /workspace/ros2_ws/install/setup.bash" >> /root/.bashrc && \
    echo "export ACADOS_SOURCE_DIR=/opt/acados" >> /root/.bashrc && \
    echo "export LD_LIBRARY_PATH=/opt/acados/lib:\$LD_LIBRARY_PATH" >> /root/.bashrc && \
    echo "export PYTHONPATH=/opt/acados/interfaces/acados_template:\$PYTHONPATH" >> /root/.bashrc

ENTRYPOINT ["/workspace/scripts/entrypoint.sh"]
CMD ["bash"]
