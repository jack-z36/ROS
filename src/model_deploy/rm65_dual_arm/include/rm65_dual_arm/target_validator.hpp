// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0
//
// 目标位姿执行前校验。实现契约 rm65_driver_node 命令执行契约.md §执行前校验：
//   - frame_id 必须是 left_arm_base / right_arm_base 之一（与目标侧匹配）
//   - pose 含 NaN/Inf 拒绝
//   - quaternion 范数异常拒绝
//   - target 过期（header.stamp 超过 stale_target_sec）拒绝
// 校验只针对单条 PoseStamped 本身的静态属性与时间属性；不涉及位移上限
// （那是 delta_guard 的职责）和许可/急停（那是 permit_guard 的职责）。

#ifndef RM65_DUAL_ARM__TARGET_VALIDATOR_HPP_
#define RM65_DUAL_ARM__TARGET_VALIDATOR_HPP_

#include <string>

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "builtin_interfaces/msg/time.hpp"

namespace rm65_dual_arm
{

// 校验失败时填充的稳定 reason code，用于 health.msg 的 reason 字段。
// 这些 code 不进 CommandPermit（那是 permit_guard 的职责），只是本节点
// 自己记录的拒绝原因。
struct ValidationResult
{
  bool ok{false};
  std::string reason_code;   // 稳定 code（见下），health.reason 会被人类可读描述覆盖
  std::string reason;        // 人类可读简短描述
};

// 对目标 PoseStamped 做静态校验。
//
// 参数：
//   target              目标位姿
//   expected_frame_id   期望的 frame_id（"left_arm_base" 或 "right_arm_base"）
//   now_sec             当前时间（秒，double），用于 stale 判断
//   stale_target_sec    目标最大可用年龄（秒）
//
// 返回 ValidationResult。reason_code 取值：
//   FRAME_MISMATCH   frame_id 与期望不符
//   POSE_NON_FINITE  position 或 quaternion 含 NaN/Inf
//   QUATERNION_BAD   quaternion 模长异常（近 0 或非单位）
//   TARGET_STALE     header.stamp 超过 stale_target_sec
//   TARGET_UNSTAMPED header.stamp 为 0（未填时间戳），无法判 stale 直接拒绝
ValidationResult validate_target(const geometry_msgs::msg::PoseStamped & target,
                                 const std::string & expected_frame_id,
                                 double now_sec,
                                 double stale_target_sec);

}  // namespace rm65_dual_arm

#endif  // RM65_DUAL_ARM__TARGET_VALIDATOR_HPP_
