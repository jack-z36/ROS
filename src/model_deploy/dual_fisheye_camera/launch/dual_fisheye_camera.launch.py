"""Launch file for the dual fisheye camera package.

启动内容：
  1. 两个 ``v4l2-ctl --set-parm <frame_rate>`` 进程（左/右），用于在打开设备前设定帧率。
     每个进程退出后通过 OnProcessExit 门控启动对应的 v4l2_camera_node。
  2. 两个 ``v4l2_camera_node`` 实例（左/右），图像采集复用上游驱动，不发相机控制指令。
     image_raw 被 remap 到配置的 left/right image topic。
  3. 一个 ``camera_health_node``（本包），订阅两侧 image，发布 /hardware/camera/health。

设计说明：
  - 沿用 gopro_pose_record.launch.py 的 OpaqueFunction + 预解析参数模式，避免左右两路
    在同一 launch context 下参数串扰（多实例安全）。
  - 设备路径默认值来自 config/dual_fisheye_camera.yaml；launch 参数可覆盖。
    生产配置必须使用 /dev/v4l/by-path/... 或 /dev/v4l/by-id/...，禁止裸 /dev/videoX。
"""

import os

import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _load_yaml_params(context):
    """加载包内默认 config yaml 作为参数文件（可被 launch 参数覆盖）。"""
    params_file = LaunchConfiguration('params_file').perform(context)
    if not params_file or not os.path.exists(params_file):
        # 未显式提供或路径不存在时，回退到包内默认 yaml
        share = get_package_share_directory('dual_fisheye_camera')
        params_file = os.path.join(share, 'config', 'dual_fisheye_camera.yaml')
    return params_file


def _yaml_default_param(params_file, key):
    """从参数 yaml 读 dual_fisheye_camera.ros__parameters 下的默认值。

    v4l2_camera_node 的节点名/命名空间与 yaml 顶层键不匹配，yaml 里的
    left/right_video_device 不会自动生效，必须在 launch 层显式读出。
    """
    with open(params_file, 'r', encoding='utf-8') as fh:
        data = yaml.safe_load(fh) or {}
    return (
        data.get('dual_fisheye_camera', {})
        .get('ros__parameters', {})
        .get(key, '')
    )


def _make_camera_pair(context, side: str):
    """构造一侧的 v4l2-ctl 设帧率进程 + v4l2_camera_node，含启动门控。

    返回 (set_frame_rate_action, camera_node_action)。
    camera_node 应在 set_frame_rate 退出后启动（调用方负责 RegisterEventHandler）。
    """
    # 预解析参数（多实例安全）
    params_file = _load_yaml_params(context)
    video_device = LaunchConfiguration(f'{side}_video_device').perform(context)
    if not video_device:
        # launch 参数未覆盖时，回退到 yaml 里的设备路径（否则空路径会
        # 直接覆盖 yaml，导致 "Cannot open device"）
        video_device = _yaml_default_param(params_file, f'{side}_video_device')
    frame_rate = LaunchConfiguration('frame_rate').perform(context)
    frame_id = LaunchConfiguration(f'{side}_frame_id').perform(context)
    image_topic = LaunchConfiguration(f'{side}_image_topic').perform(context)
    namespace = LaunchConfiguration(f'{side}_namespace').perform(context)
    node_name = LaunchConfiguration(f'{side}_node_name').perform(context)

    # 1) 先用 v4l2-ctl 设帧率（jazzy v4l2_camera 不暴露 publish_rate，
    #    单靠 yaml 的 time_per_frame 不可靠，故沿用阶段一做法显式设一次）
    set_frame_rate = ExecuteProcess(
        cmd=['v4l2-ctl', '-d', video_device, '--set-parm', frame_rate],
        output='screen',
    )

    # 2) 对应的 v4l2_camera_node（参数文件在前，内联字典覆盖设备/帧相关项）
    camera_node = Node(
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name=node_name,
        namespace=namespace,
        output='screen',
        parameters=[
            params_file,
            {
                'video_device': video_device,
                'camera_name': f'{side}_fisheye',
                'frame_id': frame_id,
                'use_v4l2_buffer_timestamps': True,
                'use_sensor_data_qos': True,
                'publish_camera_info': False,
            },
        ],
        remappings=[
            ('image_raw', image_topic),
        ],
    )

    return set_frame_rate, camera_node


def _launch_setup(context):
    params_file = _load_yaml_params(context)
    health_topic = LaunchConfiguration('health_topic').perform(context)

    # 左右两路采集
    left_set_parm, left_node = _make_camera_pair(context, 'left')
    right_set_parm, right_node = _make_camera_pair(context, 'right')

    # health 监控节点（本包），加载同一份参数文件（读取 health_hz/frame_timeout_sec/topic）
    health_node = Node(
        package='dual_fisheye_camera',
        executable='camera_health_node',
        name='camera_health_node',
        output='screen',
        parameters=[
            params_file,
            {'health_topic': health_topic},
        ],
    )

    # 门控：设帧率进程退出后再启动对应相机节点（两路相互独立，互不阻塞）
    return [
        left_set_parm,
        right_set_parm,
        RegisterEventHandler(
            OnProcessExit(target_action=left_set_parm, on_exit=[left_node])
        ),
        RegisterEventHandler(
            OnProcessExit(target_action=right_set_parm, on_exit=[right_node])
        ),
        health_node,
    ]


def _default_params_file():
    return PathJoinSubstitution([
        FindPackageShare('dual_fisheye_camera'), 'config', 'dual_fisheye_camera.yaml'
    ])


def generate_launch_description() -> LaunchDescription:
    """生成 launch 描述。所有参数均有默认值，可被命令行 ``key:=value`` 覆盖。"""
    return LaunchDescription([
        # 参数文件（默认指向包内 config）
        DeclareLaunchArgument('params_file', default_value=str(_default_params_file())),

        # 左设备 / 右设备（默认值来自 yaml；此处占位，生产请用 by-path/by-id）
        DeclareLaunchArgument('left_video_device', default_value=''),
        DeclareLaunchArgument('right_video_device', default_value=''),

        # frame_id
        DeclareLaunchArgument('left_frame_id', default_value='left_fisheye'),
        DeclareLaunchArgument('right_frame_id', default_value='right_fisheye'),

        # 帧率 / 像素格式相关（透传给 v4l2_camera_node + v4l2-ctl）
        DeclareLaunchArgument('frame_rate', default_value='30'),

        # 发布 topic
        DeclareLaunchArgument('left_image_topic', default_value='/image/left_fisheye'),
        DeclareLaunchArgument('right_image_topic', default_value='/image/right_fisheye'),
        DeclareLaunchArgument('health_topic', default_value='/hardware/camera/health'),

        # 节点命名空间 / 名称（左右独立，避免冲突）
        DeclareLaunchArgument('left_namespace', default_value='dual_fisheye_left'),
        DeclareLaunchArgument('right_namespace', default_value='dual_fisheye_right'),
        DeclareLaunchArgument('left_node_name', default_value='left_fisheye_camera'),
        DeclareLaunchArgument('right_node_name', default_value='right_fisheye_camera'),

        OpaqueFunction(function=_launch_setup),
    ])
