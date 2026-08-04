// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0

#include "rm65_dual_arm/target_validator.hpp"

#include <cmath>

#include "rm65_dual_arm/pose_conversion.hpp"

namespace rm65_dual_arm
{

namespace
{
// builtin_interfaces/Time 是 sec (uint32) + nanosec (uint32)，转 double 秒。
double stamp_to_sec(const builtin_interfaces::msg::Time & stamp)
{
  return static_cast<double>(stamp.sec) +
         static_cast<double>(stamp.nanosec) * 1e-9;
}
}  // namespace

ValidationResult validate_target(const geometry_msgs::msg::PoseStamped & target,
                                 const std::string & expected_frame_id,
                                 double now_sec,
                                 double stale_target_sec)
{
  ValidationResult res;

  // 1) frame_id
  if (target.header.frame_id != expected_frame_id) {
    res.ok = false;
    res.reason_code = "FRAME_MISMATCH";
    res.reason = std::string("frame_id '") + target.header.frame_id +
                 "' does not match expected '" + expected_frame_id + "'";
    return res;
  }

  // 2) stamp 必须非零（ROS 未填 stamp 会让 stale 判断无意义）
  const double stamp_sec = stamp_to_sec(target.header.stamp);
  if (stamp_sec <= 0.0 || !std::isfinite(stamp_sec)) {
    res.ok = false;
    res.reason_code = "TARGET_UNSTAMPED";
    res.reason = "target header.stamp is zero or invalid";
    return res;
  }

  // 3) stale 判断（绝对差，不假设 now >= stamp，避免时钟回拨误判）
  const double age = std::abs(now_sec - stamp_sec);
  if (age > stale_target_sec) {
    res.ok = false;
    res.reason_code = "TARGET_STALE";
    res.reason = std::string("target age ") + std::to_string(age) +
                 "s exceeds stale_target_sec " + std::to_string(stale_target_sec) + "s";
    return res;
  }

  // 4) position finite
  const auto & p = target.pose.position;
  if (!std::isfinite(p.x) || !std::isfinite(p.y) || !std::isfinite(p.z)) {
    res.ok = false;
    res.reason_code = "POSE_NON_FINITE";
    res.reason = "target position contains NaN/Inf";
    return res;
  }

  // 5) quaternion finite + norm（复用 pose_conversion 的校验）
  std::string q_reason;
  if (!is_valid_ros_quaternion(target.pose.orientation, q_reason)) {
    res.ok = false;
    res.reason_code = "QUATERNION_BAD";
    res.reason = q_reason.empty() ? std::string("quaternion invalid") : q_reason;
    return res;
  }

  res.ok = true;
  return res;
}

}  // namespace rm65_dual_arm
