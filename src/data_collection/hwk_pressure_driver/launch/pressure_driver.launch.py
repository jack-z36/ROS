from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    default_config_file = PathJoinSubstitution(
        [FindPackageShare("hwk_pressure_driver"), "config", "pressure_sensors.yaml"]
    )

    config_file = LaunchConfiguration("config_file")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config_file",
                default_value=default_config_file,
                description="Path to the HWK pressure sensor YAML configuration file.",
            ),
            Node(
                package="hwk_pressure_driver",
                executable="pressure_driver_node",
                name="pressure_driver_node",
                output="screen",
                parameters=[{"config_file": config_file}],
            ),
        ]
    )
