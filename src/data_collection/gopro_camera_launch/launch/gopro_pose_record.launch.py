from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _as_bool(value: str) -> bool:
    return str(value).lower() in ('1', 'true', 'yes', 'on')


def _launch_setup(context):
    package_share = FindPackageShare('gopro_camera_launch')
    camera_config = PathJoinSubstitution([package_share, 'config', 'gopro_camera.yaml'])

    video_device = LaunchConfiguration('video_device').perform(context)
    frame_rate = LaunchConfiguration('frame_rate').perform(context)
    publish_camera_info = _as_bool(LaunchConfiguration('publish_camera_info').perform(context))
    camera_namespace = LaunchConfiguration('camera_namespace').perform(context)
    node_name = LaunchConfiguration('node_name').perform(context)
    camera_name = LaunchConfiguration('camera_name').perform(context)
    frame_id = LaunchConfiguration('frame_id').perform(context)
    pixel_format = LaunchConfiguration('pixel_format').perform(context)
    output_encoding = LaunchConfiguration('output_encoding').perform(context)
    image_raw_topic = LaunchConfiguration('image_raw_topic').perform(context)
    camera_info_topic = LaunchConfiguration('camera_info_topic').perform(context)

    set_frame_rate = ExecuteProcess(
        cmd=[
            'v4l2-ctl',
            '-d',
            video_device,
            '--set-parm',
            frame_rate,
        ],
        output='screen',
    )

    camera_node = Node(
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name=node_name,
        namespace=camera_namespace,
        output='screen',
        parameters=[
            camera_config,
            {
                'video_device': video_device,
                'camera_name': camera_name,
                'frame_id': frame_id,
                'pixel_format': pixel_format,
                'output_encoding': output_encoding,
                'use_v4l2_buffer_timestamps': True,
                'use_sensor_data_qos': True,
                'publish_camera_info': publish_camera_info,
            },
        ],
        remappings=[
            ('image_raw', image_raw_topic),
            ('camera_info', camera_info_topic),
        ],
    )

    return [
        set_frame_rate,
        RegisterEventHandler(
            OnProcessExit(
                target_action=set_frame_rate,
                on_exit=[camera_node],
            )
        ),
    ]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument('video_device', default_value='/dev/video4'),
            DeclareLaunchArgument('frame_rate', default_value='30'),
            DeclareLaunchArgument('publish_camera_info', default_value='true'),
            DeclareLaunchArgument('camera_namespace', default_value='gopro'),
            DeclareLaunchArgument('node_name', default_value='gopro_camera'),
            DeclareLaunchArgument('camera_name', default_value='gopro'),
            DeclareLaunchArgument('frame_id', default_value='camera_optical_frame'),
            DeclareLaunchArgument('pixel_format', default_value='YUYV'),
            DeclareLaunchArgument('output_encoding', default_value='rgb8'),
            DeclareLaunchArgument('image_raw_topic', default_value='image_raw'),
            DeclareLaunchArgument('camera_info_topic', default_value='camera_info'),
            OpaqueFunction(function=_launch_setup),
        ]
    )
