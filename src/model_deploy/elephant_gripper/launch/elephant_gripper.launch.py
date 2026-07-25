from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    default_config_file = PathJoinSubstitution(
        [FindPackageShare("elephant_gripper"), "config", "elephant_gripper.yaml"]
    )

    config_file = LaunchConfiguration("config_file")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config_file",
                default_value=default_config_file,
                description="Path to the Elephant gripper YAML configuration file.",
            ),
            Node(
                package="elephant_gripper",
                executable="elephant_gripper_node",
                name="elephant_gripper_node",
                output="screen",
                parameters=[{"config_file": config_file}],
            ),
        ]
    )
