// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0

#include "rm65_dual_arm/delta_guard.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>

#include "rm65_dual_arm/pose_conversion.hpp"

namespace rm65_dual_arm
{

namespace
{
bool is_finite_v(double v) { return std::isfinite(v); }
}  // namespace

bool compute_pose_delta(const geometry_msgs::msg::Pose & current,
                        const geometry_msgs::msg::Pose & target,
                        double & out_xyz_m,
                        double & out_angle_rad,
                        std::string & reason)
{
  const auto & cp = current.position;
  const auto & tp = target.position;
  if (!is_finite_v(cp.x) || !is_finite_v(cp.y) || !is_finite_v(cp.z) ||
    !is_finite_v(tp.x) || !is_finite_v(tp.y) || !is_finite_v(tp.z))
  {
    reason = "position contains NaN/Inf";
    return false;
  }
  const double dx = tp.x - cp.x;
  const double dy = tp.y - cp.y;
  const double dz = tp.z - cp.z;
  out_xyz_m = std::sqrt(dx * dx + dy * dy + dz * dz);

  // 校验两个四元数合法
  std::string r1, r2;
  if (!is_valid_ros_quaternion(current.orientation, r1)) {
    reason = std::string("current quaternion invalid: ") + r1;
    return false;
  }
  if (!is_valid_ros_quaternion(target.orientation, r2)) {
    reason = std::string("target quaternion invalid: ") + r2;
    return false;
  }

  // q_rel = q_current^-1 * q_target
  // 四元数逆 = 共轭（单位四元数）
  const double cw = current.orientation.w;
  const double cx = current.orientation.x;
  const double cy = current.orientation.y;
  const double cz = current.orientation.z;
  const double tw = target.orientation.w;
  const double tx = target.orientation.x;
  const double ty = target.orientation.y;
  const double tz = target.orientation.z;

  // (cw,-cx,-cy,-cz) * (tw,tx,ty,tz)
  const double rw = cw * tw + cx * tx + cy * ty + cz * tz;
  const double rx = cw * tx - cx * tw - cy * tz + cz * ty;
  const double ry = cw * ty + cx * tz - cy * tw - cz * tx;
  const double rz = cw * tz - cx * ty + cy * tx - cz * tw;

  // 相对旋转的夹角 = 2 * acos(|rw|)（取绝对值处理双覆盖）
  const double w_clamped = std::max(-1.0, std::min(1.0, std::abs(rw)));
  out_angle_rad = 2.0 * std::acos(w_clamped);

  reason.clear();
  return true;
}

DeltaResult check_delta(bool has_current,
                        const RmPose & current_tcp,
                        const geometry_msgs::msg::Pose & target,
                        double max_step_xyz_m,
                        double max_step_angle_rad)
{
  DeltaResult res;
  if (!has_current) {
    res.ok = false;
    res.reason_code = "CURRENT_MISSING";
    res.reason = "no real TCP reading yet; refusing to move without a known baseline";
    return res;
  }

  // 当前 TCP -> ROS Pose（同时做合法性校验）
  geometry_msgs::msg::Pose current_ros;
  std::string conv_reason;
  if (!rm_pose_to_ros_pose(current_tcp, current_ros, conv_reason)) {
    res.ok = false;
    res.reason_code = "CURRENT_QUATERNION_BAD";
    res.reason = std::string("current TCP invalid: ") + conv_reason;
    return res;
  }

  if (!compute_pose_delta(current_ros, target, res.xyz_m, res.angle_rad, conv_reason)) {
    res.ok = false;
    res.reason_code = "CURRENT_NON_FINITE";
    res.reason = std::string("delta computation failed: ") + conv_reason;
    return res;
  }

  const bool xyz_exceeded = res.xyz_m > max_step_xyz_m;
  const bool angle_exceeded = res.angle_rad > max_step_angle_rad;
  if (xyz_exceeded || angle_exceeded) {
    res.ok = false;
    res.reason_code = "DELTA_EXCEEDED";
    std::ostringstream oss;
    oss << "step too large: xyz=" << res.xyz_m << "m (limit " << max_step_xyz_m
        << "m), angle=" << res.angle_rad << "rad (limit " << max_step_angle_rad
        << "rad)";
    res.reason = oss.str();
    return res;
  }

  res.ok = true;
  return res;
}

}  // namespace rm65_dual_arm
