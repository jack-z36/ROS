# Copyright (c) model_deploy Maintainers
# SPDX-License-Identifier: Apache-2.0
"""RM65 双臂节点 launch。

默认行为：
  - 从 config/rm65_dual_arm.yaml 加载参数
  - 把 /arm/{left,right}_tcp_pose 默认 remap 到 /act/observation/arm/{left,right}_tcp_pose，
    让 ACT 节点零配置订阅；设置 remap_to_act:=false 可关闭

启动：
  ros2 launch rm65_dual_arm rm65_dual_arm.launch.py
  ros2 launch rm65_dual_arm rm65_dual_arm.launch.py remap_to_act:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _load_default_params():
    """读取包内默认 yaml，作为 --params-file 默认值。"""
    share = get_package_share_directory('rm65_dual_arm')
    path = os.path.join(share, 'config', 'rm65_dual_arm.yaml')
    return path


def generate_launch_description():
    params_file = LaunchConfiguration('params_file')
    remap_to_act = LaunchConfiguration('remap_to_act')

    default_params = _load_default_params()

    declare_params = DeclareLaunchArgument(
        'params_file',
        default_value=default_params,
        description='rm65_dual_arm_node 参数文件路径',
    )

    # 默认把 /arm/*_tcp_pose remap 到 /act/observation/arm/*_tcp_pose，让 ACT
    # 节点零配置订阅。若想保留 /arm/* 原名，可在自定义 params_file 里把
    # topics.left_tcp_pose / topics.right_tcp_pose 设为 /arm/* 并覆盖 remap。
    remappings = [
        ('/arm/left_tcp_pose', '/act/observation/arm/left_tcp_pose'),
        ('/arm/right_tcp_pose', '/act/observation/arm/right_tcp_pose'),
    ]

    node = Node(
        package='rm65_dual_arm',
        executable='rm65_dual_arm_node',
        name='rm65_dual_arm_node',
        output='screen',
        parameters=[params_file],
        remappings=remappings,
    )

    return LaunchDescription([
        declare_params,
        node,
    ])
