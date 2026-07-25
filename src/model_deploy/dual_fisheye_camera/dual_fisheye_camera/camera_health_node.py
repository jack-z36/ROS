"""Camera health monitoring node for the dual fisheye camera package.

This node does NOT acquire images itself. Image acquisition is handled by two
``v4l2_camera_node`` instances started by the launch file (reuse over rewrite,
per the fisheye_camera_node contract). This node subscribes to the left/right
image topics, measures per-side frame freshness, and publishes an
``act_interfaces/HardwareHealth`` summary to ``/hardware/camera/health``.

HardwareHealth 字段语义借用（相机场景）：
    header.stamp            health 发布时刻
    left/right_connected    该侧在 frame_timeout_sec 内是否收到过帧
    left/right_estop_active 固定 False（相机无急停概念）
    left/right_sdk_code     固定 0（相机无 SDK 返回码）
    left/right_controller_err 固定 0（相机无控制器错误码）
    left/right_reason       "" 正常 / "NO_FRAME_YET" / "STREAM_TIMEOUT"
"""

from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

# act_interfaces 由独立 PR（act-interfaces）提供，且需先 colcon build。
# 本包 package.xml 已声明 exec_depend act_interfaces。若本地尚未 build，
# 见 README「依赖」一节。
from act_interfaces.msg import HardwareHealth


# reason 稳定码（写入 HardwareHealth.{left,right}_reason）
_REASON_OK = ''
_REASON_NO_FRAME = 'NO_FRAME_YET'       # 启动后从未收到该侧帧
_REASON_TIMEOUT = 'STREAM_TIMEOUT'      # 曾经收到过，但已超 frame_timeout_sec


def _stamp_to_sec(stamp) -> float:
    """ros Time/Duration 的 nanoseconds 拆成秒（跨 builtin_interfaces/rospy 兼容写法）。"""
    return stamp.sec + stamp.nanosec * 1e-9


class CameraHealthNode(Node):
    """订阅左右 image，发布相机 HardwareHealth。"""

    def __init__(self) -> None:
        super().__init__('camera_health_node')

        # ---- 参数声明（默认值对齐 config/dual_fisheye_camera.yaml） ----
        self.declare_parameter('left_image_topic', '/image/left_fisheye')
        self.declare_parameter('right_image_topic', '/image/right_fisheye')
        self.declare_parameter('health_topic', '/hardware/camera/health')
        self.declare_parameter('health_hz', 5.0)
        self.declare_parameter('frame_timeout_sec', 1.0)

        left_image_topic = self.get_parameter('left_image_topic').value
        right_image_topic = self.get_parameter('right_image_topic').value
        health_topic = self.get_parameter('health_topic').value
        health_hz = float(self.get_parameter('health_hz').value)
        self._frame_timeout_sec = float(self.get_parameter('frame_timeout_sec').value)

        if health_hz <= 0.0:
            raise ValueError(f'health_hz must be > 0, got {health_hz}')
        if self._frame_timeout_sec <= 0.0:
            raise ValueError(
                f'frame_timeout_sec must be > 0, got {self._frame_timeout_sec}'
            )

        # ---- 每侧最近一帧时间（None 表示启动后从未收到） ----
        self._last_frame_sec: dict[str, Optional[float]] = {
            'left': None,
            'right': None,
        }

        # ---- 订阅左右 image（QoS 必须与 v4l2_camera_node 的 sensor_data 对齐） ----
        self.create_subscription(
            Image,
            left_image_topic,
            lambda msg: self._on_image('left', msg),
            qos_profile_sensor_data,
        )
        self.create_subscription(
            Image,
            right_image_topic,
            lambda msg: self._on_image('right', msg),
            qos_profile_sensor_data,
        )

        # ---- 发布 health（reliable，深度 10，供监控/UI 稳定消费） ----
        self._health_pub = self.create_publisher(HardwareHealth, health_topic, 10)

        # ---- 周期发布 ----
        self._health_timer = self.create_timer(1.0 / health_hz, self._publish_health)

        self.get_logger().info(
            f'camera_health_node up: sub L={left_image_topic} R={right_image_topic}, '
            f'pub={health_topic} @ {health_hz:.1f}Hz, timeout={self._frame_timeout_sec:.2f}s'
        )

    # ---- 订阅回调：只记录最近帧时间，不做重活 ----
    def _on_image(self, side: str, msg: Image) -> None:
        # 优先用图像 header.stamp（V4L2 buffer timestamp）；若为 0 则退化到 ROS clock。
        stamp = msg.header.stamp
        if stamp.sec == 0 and stamp.nanosec == 0:
            now = self.get_clock().now()
            self._last_frame_sec[side] = now.nanoseconds * 1e-9
        else:
            self._last_frame_sec[side] = _stamp_to_sec(stamp)

    # ---- 周期发布 health ----
    def _publish_health(self) -> None:
        now_sec = self.get_clock().now().nanoseconds * 1e-9

        left_state = self._eval_side('left', now_sec)
        right_state = self._eval_side('right', now_sec)

        msg = HardwareHealth()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'dual_fisheye_camera'

        msg.left_connected = left_state.connected
        msg.right_connected = right_state.connected

        # 相机无急停 / SDK 返回码 / 控制器错误码概念，固定填 0/False。
        msg.left_estop_active = False
        msg.right_estop_active = False
        msg.left_sdk_code = 0
        msg.right_sdk_code = 0
        msg.left_controller_err = 0
        msg.right_controller_err = 0

        msg.left_reason = left_state.reason
        msg.right_reason = right_state.reason

        self._health_pub.publish(msg)

    def _eval_side(self, side: str, now_sec: float) -> '_SideState':
        last = self._last_frame_sec[side]
        if last is None:
            return _SideState(connected=False, reason=_REASON_NO_FRAME)
        age = now_sec - last
        if age > self._frame_timeout_sec:
            return _SideState(connected=False, reason=_REASON_TIMEOUT)
        return _SideState(connected=True, reason=_REASON_OK)


class _SideState:
    """单侧 health 评估结果（内部用，便于扩展）。"""

    __slots__ = ('connected', 'reason')

    def __init__(self, connected: bool, reason: str) -> None:
        self.connected = connected
        self.reason = reason


def main(args=None) -> None:
    rclpy.init(args=args)
    node = CameraHealthNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
