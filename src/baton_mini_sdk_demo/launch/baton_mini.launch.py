from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    server_ip = LaunchConfiguration("server_ip")
    local_ip = LaunchConfiguration("local_ip")
    node_name = LaunchConfiguration("node_name")
    imu_topic = LaunchConfiguration("imu_topic")
    odom_topic = LaunchConfiguration("odom_topic")
    fast_odom_topic = LaunchConfiguration("fast_odom_topic")
    image_left_topic = LaunchConfiguration("image_left_topic")
    image_right_topic = LaunchConfiguration("image_right_topic")
    publish_imu = LaunchConfiguration("publish_imu")
    publish_odometry = LaunchConfiguration("publish_odometry")
    publish_fast_odom = LaunchConfiguration("publish_fast_odom")
    publish_image_left = LaunchConfiguration("publish_image_left")
    publish_image_right = LaunchConfiguration("publish_image_right")

    return LaunchDescription([
        DeclareLaunchArgument("server_ip", default_value="192.168.1.10"),
        DeclareLaunchArgument("local_ip", default_value="192.168.1.18"),
        DeclareLaunchArgument("node_name", default_value="baton_mini"),
        DeclareLaunchArgument("imu_topic", default_value="/baton_mini/imu"),
        DeclareLaunchArgument("odom_topic", default_value="/baton_mini/odometry"),
        DeclareLaunchArgument("fast_odom_topic", default_value="/baton_mini/fast_odom"),
        DeclareLaunchArgument("image_left_topic", default_value="/baton_mini/image_left"),
        DeclareLaunchArgument("image_right_topic", default_value="/baton_mini/image_right"),
        DeclareLaunchArgument("publish_imu", default_value="true"),
        DeclareLaunchArgument("publish_odometry", default_value="true"),
        DeclareLaunchArgument("publish_fast_odom", default_value="true"),
        DeclareLaunchArgument("publish_image_left", default_value="true"),
        DeclareLaunchArgument("publish_image_right", default_value="true"),
        Node(
            package="baton_mini",
            executable="baton_mini",
            name=node_name,
            output="screen",
            parameters=[{
                "server_ip": server_ip,
                "local_ip": local_ip,
                "imu_topic": imu_topic,
                "odom_topic": odom_topic,
                "fast_odom_topic": fast_odom_topic,
                "image_left_topic": image_left_topic,
                "image_right_topic": image_right_topic,
                "publish_imu": ParameterValue(publish_imu, value_type=bool),
                "publish_odometry": ParameterValue(publish_odometry, value_type=bool),
                "publish_fast_odom": ParameterValue(publish_fast_odom, value_type=bool),
                "publish_image_left": ParameterValue(publish_image_left, value_type=bool),
                "publish_image_right": ParameterValue(publish_image_right, value_type=bool),
            }],
        ),
    ])
