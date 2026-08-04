// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0
//
// ★ 微小运动安全闸（delta_guard）。
//
// 这是 RM65 双臂节点最核心的安全机制，直接落实"测试控制指令必须尽可能小、
// 避免大范围运动"的硬性要求。
//
// 每一条来自 ACT 的目标 PoseStamped，在通过 target_validator 之后、调用
// rm_movel 之前，必须先通过本闸：把目标位姿与"当前真实 TCP 位姿"做差，
// 位移或旋转角度超过上限即拒绝下发，绝不产生大范围运动。
//
// 默认上限（config/rm65_dual_arm.yaml safety 段）：
//   max_step_xyz_m     0.010   (1cm)
//   max_step_angle_rad 0.05    (~2.9°)
// 启动期硬上限（rm65_dual_arm_node 启动校验）：
//   max_step_xyz_m     ≤ 0.05  (5cm)
//   max_step_angle_rad ≤ 0.2   (~11.5°)
// 任何超过启动期硬上限的配置直接拒绝启动，防止误配成大运动。
//
// 注意：当前 TCP 必须来自真实 SDK 读数（rm_get_current_arm_state），不允许
// 假设零位。若 current_tcp 未初始化（has_current=false）或含 NaN，直接拒绝。

#ifndef RM65_DUAL_ARM__DELTA_GUARD_HPP_
#define RM65_DUAL_ARM__DELTA_GUARD_HPP_

#include <string>

#include "geometry_msgs/msg/pose.hpp"
#include "rm65_dual_arm/pose_conversion.hpp"  // RmPose

namespace rm65_dual_arm
{

// 启动期硬上限（rm65_dual_arm_node 在校验 config 时引用）。超过则拒绝启动。
// 这两个常量防止 YAML 误配成大运动；如未来需上调，必须双人评审 + 物理急停就位。
constexpr double kHardMaxStepXyzM = 0.05;      // 5cm
constexpr double kHardMaxStepAngleRad = 0.2;  // ~11.5°

struct DeltaResult
{
  bool ok{false};
  double xyz_m{0.0};        // 实测位移（m），无论是否超限都填，便于日志/health
  double angle_rad{0.0};    // 实测旋转角度（rad）
  std::string reason_code;  // CURRENT_MISSING / CURRENT_NON_FINITE / DELTA_EXCEEDED
  std::string reason;       // 人类可读描述
};

// 计算两个位姿之间的位移（m）和旋转角度（rad，四元数夹角的 2 倍）。
// 旋转：q_rel = q_current^-1 * q_target，夹角 = 2 * acos(|q_rel.w|)。
// 两者都需要对应四元数合法且有限，否则返回 false。
bool compute_pose_delta(const geometry_msgs::msg::Pose & current,
                        const geometry_msgs::msg::Pose & target,
                        double & out_xyz_m,
                        double & out_angle_rad,
                        std::string & reason);

// 主闸门：相对当前真实 TCP 检查目标位姿的位移/旋转是否在允许范围内。
//
// 参数：
//   has_current        是否已有真实 TCP 读数（首次或重连后可能为 false）
//   current_tcp        当前真实 TCP（rm_pose_t 镜像，含合法 quaternion）
//   target             目标 ROS pose
//   max_step_xyz_m     单步位移上限（m）
//   max_step_angle_rad 单步角度上限（rad）
//
// reason_code：
//   CURRENT_MISSING     未读取到真实 TCP（首次/重连后），拒绝避免假设零位
//   CURRENT_NON_FINITE  当前 TCP 含 NaN/Inf
//   CURRENT_QUATERNION_BAD 当前 TCP 四元数非法
//   DELTA_EXCEEDED      位移或角度超限（核心拒绝路径）
DeltaResult check_delta(bool has_current,
                        const RmPose & current_tcp,
                        const geometry_msgs::msg::Pose & target,
                        double max_step_xyz_m,
                        double max_step_angle_rad);

}  // namespace rm65_dual_arm

#endif  // RM65_DUAL_ARM__DELTA_GUARD_HPP_
