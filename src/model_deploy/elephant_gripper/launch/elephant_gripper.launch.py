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
                # 默认把 /gripper/*_state remap 到 /act/observation/gripper/*_state，
                # 让 ACT 大脑零配置订阅（节点发布类型为 Pose，宽度在 position.x）。
                remappings=[
                    ("/gripper/left_state", "/act/observation/gripper/left_state"),
                    ("/gripper/right_state", "/act/observation/gripper/right_state"),
                ],
            ),
        ]
    )
