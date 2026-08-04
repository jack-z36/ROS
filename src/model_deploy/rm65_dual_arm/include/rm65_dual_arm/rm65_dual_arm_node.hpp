// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0
//
// RM65 双臂主节点。单节点承载：
//   - 发布 /arm/left_tcp_pose、/arm/right_tcp_pose（Pose，无 header；ACT 大脑按 Pose
//     订阅，坐标系约定为各自 left/right_arm_base；历史上曾为 PoseStamped）
//   - 发布 /hardware/rm65/health（HardwareHealth）
//   - 订阅 /act/command/arm/left_target、/right_target（PoseStamped）
//   - 订阅 /act/command/permit（CommandPermit）
//   - 提供 /hardware/rm65/emergency_stop service（std_srvs/SetBool）
//
// 多重闸门编排（每条目标 PoseStamped 必须全部通过才下发 rm_movel）：
//   1) permit_guard：CommandPermit allowed=true 且未 stale
//   2) target_validator：frame_id / finite / quaternion norm / stale
//   3) delta_guard：相对当前真实 TCP 位移在 max_step_xyz_m / max_step_angle_rad 内
//   4) 急停未激活
//   5) SDK 已连接
// 任一失败：不发 rm_movel，不伪造 accepted，health 记 reason。

#ifndef RM65_DUAL_ARM__RM65_DUAL_ARM_NODE_HPP_
#define RM65_DUAL_ARM__RM65_DUAL_ARM_NODE_HPP_

#include <atomic>
#include <memory>
#include <mutex>
#include <string>

#include "act_interfaces/msg/command_permit.hpp"
#include "act_interfaces/msg/hardware_health.hpp"
#include "geometry_msgs/msg/pose.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "rclcpp/rclcpp.hpp"
#include "std_srvs/srv/set_bool.hpp"

#include "rm65_dual_arm/delta_guard.hpp"
#include "rm65_dual_arm/permit_guard.hpp"
#include "rm65_dual_arm/rm65_arm.hpp"

namespace rm65_dual_arm
{

struct NodeConfig
{
  // 左右臂
  std::string left_ip;
  int left_port{8080};
  std::string left_frame_id{"left_arm_base"};
  std::string right_ip;
  int right_port{8080};
  std::string right_frame_id{"right_arm_base"};

  // 运动
  int speed_percent{10};        // ★ 测试期默认最低 10
  int blend_radius_percent{0};
  bool block{false};
  double command_timeout_sec{2.0};

  // 安全
  double stale_target_sec{0.5};
  double permit_stale_sec{1.0};
  double max_step_xyz_m{0.010};     // ★ 1cm
  double max_step_angle_rad{0.05};  // ★ ~2.9°

  // 发布频率
  double pose_hz{50.0};
  double health_hz{10.0};

  // topics（默认值，可被参数覆盖）
  std::string left_tcp_pose_topic{"/arm/left_tcp_pose"};
  std::string right_tcp_pose_topic{"/arm/right_tcp_pose"};
  std::string health_topic{"/hardware/rm65/health"};
  std::string left_target_topic{"/act/command/arm/left_target"};
  std::string right_target_topic{"/act/command/arm/right_target"};
  std::string permit_topic{"/act/command/permit"};
  std::string emergency_stop_service{"/hardware/rm65/emergency_stop"};
};

class Rm65DualArmNode : public rclcpp::Node
{
public:
  explicit Rm65DualArmNode(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());
  ~Rm65DualArmNode() override;

private:
  // 参数加载与校验。任一硬性校验失败抛 std::runtime_error，让 main 捕获后退出。
  NodeConfig load_and_validate_config();

  // 回调
  void on_left_target(const geometry_msgs::msg::PoseStamped::SharedPtr msg);
  void on_right_target(const geometry_msgs::msg::PoseStamped::SharedPtr msg);
  void on_permit(const act_interfaces::msg::CommandPermit::SharedPtr msg);
  void on_emergency_stop(
    const std::shared_ptr<std_srvs::srv::SetBool::Request> request,
    std::shared_ptr<std_srvs::srv::SetBool::Response> response);

  // 定时器
  void on_pose_timer();
  void on_health_timer();

  // 统一处理一侧目标，side 决定使用哪条臂与哪个 frame_id。
  // 返回拒绝时填 reject_reason；接受并下发返回空。
  std::string handle_target(Rm65Arm::Side side,
                            const geometry_msgs::msg::PoseStamped & target);

  // 节点配置
  NodeConfig config_;

  // 左右臂封装
  std::unique_ptr<Rm65Arm> left_arm_;
  std::unique_ptr<Rm65Arm> right_arm_;

  // 许可守卫
  PermitGuard permit_guard_;

  // 发布者（TCP pose 发裸 Pose；命令订阅方向仍是 PoseStamped，见下方订阅者）
  rclcpp::Publisher<geometry_msgs::msg::Pose>::SharedPtr left_pose_pub_;
  rclcpp::Publisher<geometry_msgs::msg::Pose>::SharedPtr right_pose_pub_;
  rclcpp::Publisher<act_interfaces::msg::HardwareHealth>::SharedPtr health_pub_;

  // 订阅者
  rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr left_target_sub_;
  rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr right_target_sub_;
  rclcpp::Subscription<act_interfaces::msg::CommandPermit>::SharedPtr permit_sub_;

  // service
  rclcpp::Service<std_srvs::srv::SetBool>::SharedPtr estop_service_;

  // 定时器
  rclcpp::TimerBase::SharedPtr pose_timer_;
  rclcpp::TimerBase::SharedPtr health_timer_;

  // 急停全局状态（service 设置后影响两侧闸门）
  std::atomic<bool> estop_active_{false};

  // 运动调用串行化（避免左/右回调并发竞争同一臂的 SDK 调用）
  std::mutex left_motion_mutex_;
  std::mutex right_motion_mutex_;

  // 缓存最近一次 health 内容（供 health 定时器发布）
  mutable std::mutex health_mutex_;
  act_interfaces::msg::HardwareHealth last_health_;
};

}  // namespace rm65_dual_arm

#endif  // RM65_DUAL_ARM__RM65_DUAL_ARM_NODE_HPP_
