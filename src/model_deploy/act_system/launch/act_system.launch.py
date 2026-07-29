# Copyright (c) model_deploy Maintainers
# SPDX-License-Identifier: Apache-2.0
"""act_system 总 launch：一条命令拉起 ACT 运行所需的全部节点。

启动内容：
  1. rm65_dual_arm.launch.py     — RM65 双臂节点（含 /act/observation/arm/* remap）
  2. elephant_gripper.launch.py  — 大象夹爪节点
  3. dual_fisheye_camera.launch.py — 双鱼眼相机节点（左/右 v4l2 + camera_health）
  4. ACT 部署节点 — act/ 不是 colcon 包，用 ExecuteProcess 以
     ``python3 -m model_deploy.act.ui.act_deploy_node --config <act_config>`` 启动，
     PYTHONPATH 前置 <workspace>/src。

健壮性：某硬件包可执行文件缺失（如 RM65 SDK 未拷入）时，跳过该组件并告警，
其余组件照常启动；跳过的组件由一键脚本的核对表报 FAIL。

launch 参数：
  - act_config: ACT deploy.yaml 路径，默认 src/model_deploy/act/config_files/deploy.yaml
  - act_python: ACT 节点的 Python 解释器（需含 torch，默认 python3）
  - enable_command_output: 默认 false（fail-closed）；true 时给 ACT 节点追加
    --enable-command-output 启动开关

启动：
  ros2 launch act_system act_system.launch.py
  ros2 launch act_system act_system.launch.py act_config:=/path/to/deploy.yaml
"""
import os

from ament_index_python.packages import (
    PackageNotFoundError,
    get_package_prefix,
    get_package_share_directory,
)
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _find_workspace_root():
    """从本文件位置向上找 workspace 根（同时兼容源码路径与 install 安装路径）。

    判定依据：目录下存在 src/model_deploy/act/ui/act_deploy_node.py。
    可用环境变量 ACT_WS_ROOT 显式覆盖。
    """
    env_root = os.environ.get('ACT_WS_ROOT', '')
    if env_root and os.path.isdir(env_root):
        return os.path.abspath(env_root)
    marker = os.path.join('src', 'model_deploy', 'act', 'ui', 'act_deploy_node.py')
    current = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isfile(os.path.join(current, marker)):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            raise RuntimeError(
                'act_system: 无法定位 workspace 根（未找到 %s）。'
                '请设置环境变量 ACT_WS_ROOT=<workspace 路径>。' % marker
            )
        current = parent


# act_deploy_node.py 模块顶层只 `import rclpy` 却引用 `rclpy.node.Node`，而
# `import rclpy` 不会自动导入 node 子模块；这里先预导入 rclpy.node 再调用
# 生产入口 main()（不改动 act/ 包本身）。
_ACT_BOOTSTRAP = (
    'import sys\n'
    'import rclpy.node  # noqa: F401  预导入，避免模块顶层 AttributeError\n'
    'from model_deploy.act.ui.act_deploy_node import main\n'
    'sys.exit(main(sys.argv[1:]))\n'
)


def _executable_exists(pkg, executable):
    """检查包的可执行文件是否已安装（lib/<pkg>/<executable>）。"""
    try:
        prefix = get_package_prefix(pkg)
    except PackageNotFoundError:
        return False
    return os.path.isfile(os.path.join(prefix, 'lib', pkg, executable))


def _include_hardware_launch(
    pkg,
    launch_file,
    label,
    required_executables,
    launch_arguments=None,
):
    """构造一个硬件包的 include；可执行文件缺失时跳过并告警。

    目的：单个组件未就绪（如 RM65 厂商 SDK 未拷入导致节点未编译）时，
    不能拖死整个总 launch；跳过的组件会被一键脚本的核对表报为 FAIL。
    """
    missing = [
        '%s/%s' % (exe_pkg, exe)
        for exe_pkg, exe in required_executables
        if not _executable_exists(exe_pkg, exe)
    ]
    if missing:
        return [
            LogInfo(
                msg='[act_system] 跳过 {}：可执行文件缺失 {}（包未编译或依赖未就绪）'.format(
                    label, ', '.join(missing)
                )
            )
        ]
    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory(pkg), 'launch', launch_file
                )
            ),
            launch_arguments=(launch_arguments or {}).items(),
        )
    ]


def _make_hardware_includes(context):
    """汇总三个硬件包的 include（含可用性检查）。"""
    actions = []
    actions += _include_hardware_launch(
        'rm65_dual_arm', 'rm65_dual_arm.launch.py', 'RM65 双臂节点',
        [('rm65_dual_arm', 'rm65_dual_arm_node')],
    )
    actions += _include_hardware_launch(
        'elephant_gripper', 'elephant_gripper.launch.py', '大象夹爪节点',
        [('elephant_gripper', 'elephant_gripper_node')],
    )
    actions += _include_hardware_launch(
        'dual_fisheye_camera', 'dual_fisheye_camera.launch.py', '双鱼眼相机节点',
        [
            ('dual_fisheye_camera', 'camera_health_node'),
            ('v4l2_camera', 'v4l2_camera_node'),
        ],
        launch_arguments={
            # 上游硬件适配 ACT 的 observation topic 契约；ACT 配置保持不变。
            'left_image_topic': (
                '/act/observation/image/left_gripper_fisheye'
            ),
            'right_image_topic': (
                '/act/observation/image/right_gripper_fisheye'
            ),
        },
    )
    return actions


def _make_act_node_process(context):
    """构造 ACT 部署节点进程（预解析参数，条件追加 --enable-command-output）。"""
    act_config = LaunchConfiguration('act_config').perform(context)
    act_python = LaunchConfiguration('act_python').perform(context)

    cmd = [
        act_python, '-c', _ACT_BOOTSTRAP,
        '--config', act_config,
    ]
    enable_output = LaunchConfiguration('enable_command_output').perform(context)
    if enable_output.lower() in ('true', '1', 'yes'):
        cmd.append('--enable-command-output')

    ws_root = _find_workspace_root()
    src_dir = os.path.join(ws_root, 'src')
    # lerobot 以源码形式 vendor 在 third_party，真实推理（lerobot_policy 翻译官）
    # 需要能 import lerobot，所以一并前置到 PYTHONPATH。
    lerobot_src = os.path.join(
        src_dir, 'model_deploy', 'third_party', 'lerobot', 'src')
    pythonpath = src_dir + os.pathsep + lerobot_src
    if os.environ.get('PYTHONPATH'):
        pythonpath = pythonpath + os.pathsep + os.environ['PYTHONPATH']

    return [
        ExecuteProcess(
            cmd=cmd,
            name='act_deploy_node',
            output='screen',
            additional_env={'PYTHONPATH': pythonpath},
        )
    ]


def _on_any_process_exit(event, context):
    """任一组件进程退出时打印醒目提示，便于操作者定位失败组件。"""
    return [
        LogInfo(
            msg='[act_system] 组件进程退出: {} (returncode={})'.format(
                event.process_name, event.returncode
            )
        )
    ]


def generate_launch_description():
    ws_root = _find_workspace_root()
    default_act_config = os.path.join(
        ws_root, 'src', 'model_deploy', 'act', 'config_files', 'deploy.yaml'
    )

    declare_act_config = DeclareLaunchArgument(
        'act_config',
        default_value=default_act_config,
        description='ACT 部署节点 deploy.yaml 配置文件路径',
    )
    declare_act_python = DeclareLaunchArgument(
        'act_python',
        default_value='python3',
        description='ACT 节点的 Python 解释器（需含 torch/yaml，如 model_deploy conda 环境）',
    )
    declare_enable_output = DeclareLaunchArgument(
        'enable_command_output',
        default_value='false',
        description='ACT 真实命令输出总开关（默认 false，fail-closed）',
    )

    return LaunchDescription([
        declare_act_config,
        declare_act_python,
        declare_enable_output,
        OpaqueFunction(function=_make_hardware_includes),
        OpaqueFunction(function=_make_act_node_process),
        # 不指定 target_action：匹配所有子进程退出事件
        RegisterEventHandler(OnProcessExit(on_exit=_on_any_process_exit)),
    ])
