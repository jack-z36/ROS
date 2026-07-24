// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0

#include "rm65_dual_arm/pose_conversion.hpp"

#include <cmath>

namespace rm65_dual_arm
{

namespace
{
// 标准库未提供跨平台的 std::isfinite 对 float/double 的统一调用，
// 这里用 std::isfinite(double) 即可正确处理 float 入参（隐式提升）。
bool is_finite(double v)
{
  return std::isfinite(v);
}
}  // namespace

bool is_valid_ros_quaternion(const geometry_msgs::msg::Quaternion & q,
                             std::string & reason,
                             double tol)
{
  if (!is_finite(q.x) || !is_finite(q.y) || !is_finite(q.z) || !is_finite(q.w)) {
    reason = "quaternion contains NaN/Inf";
    return false;
  }
  const double norm = std::sqrt(
    static_cast<double>(q.x) * q.x +
    static_cast<double>(q.y) * q.y +
    static_cast<double>(q.z) * q.z +
    static_cast<double>(q.w) * q.w);
  if (norm < 1e-9) {
    reason = "quaternion norm near zero";
    return false;
  }
  if (std::abs(norm - 1.0) > tol) {
    reason = "quaternion norm not unitary";
    return false;
  }
  reason.clear();
  return true;
}

geometry_msgs::msg::Quaternion rm_quat_to_ros(const RmQuat & rq)
{
  geometry_msgs::msg::Quaternion q;
  // 睿尔曼 (w, x, y, z) -> ROS (x, y, z, w)
  q.x = rq.x;
  q.y = rq.y;
  q.z = rq.z;
  q.w = rq.w;
  return q;
}

RmQuat ros_quat_to_rm(const geometry_msgs::msg::Quaternion & q)
{
  RmQuat rq;
  // ROS (x, y, z, w) -> 睿尔曼 (w, x, y, z)
  rq.w = q.w;
  rq.x = q.x;
  rq.y = q.y;
  rq.z = q.z;
  return rq;
}

geometry_msgs::msg::Quaternion euler_to_ros_quaternion(double roll, double pitch, double yaw)
{
  // roll=rx, pitch=ry, yaw=rz（ZYX 内蕴）
  const double half_r = roll * 0.5;
  const double half_p = pitch * 0.5;
  const double half_y = yaw * 0.5;
  const double cr = std::cos(half_r);
  const double sr = std::sin(half_r);
  const double cp = std::cos(half_p);
  const double sp = std::sin(half_p);
  const double cy = std::cos(half_y);
  const double sy = std::sin(half_y);

  geometry_msgs::msg::Quaternion q;
  q.x = sr * cp * cy - cr * sp * sy;
  q.y = cr * sp * cy + sr * cp * sy;
  q.z = cr * cp * sy - sr * sp * cy;
  q.w = cr * cp * cy + sr * sp * sy;
  return q;
}

RmEuler ros_quaternion_to_euler(const geometry_msgs::msg::Quaternion & q)
{
  // 标准的 ZYX 内蕴（yaw-pitch-roll）从四元数求欧拉角，与 euler_to_ros_quaternion 互逆。
  // 输入假定已通过 is_valid_ros_quaternion 校验（单位四元数）。
  const double qw = q.w;
  const double qx = q.x;
  const double qy = q.y;
  const double qz = q.z;

  // roll (x-axis rotation)
  const double sinr_cosp = 2.0 * (qw * qx + qy * qz);
  const double cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy);
  const double roll = std::atan2(sinr_cosp, cosr_cosp);

  // pitch (y-axis rotation)，处理 gimbal lock 边界
  const double sinp = 2.0 * (qw * qy - qz * qx);
  double pitch;
  if (std::abs(sinp) >= 1.0) {
    // 万向锁：用 90 度钳制
    pitch = std::copysign(M_PI_2, sinp);
  } else {
    pitch = std::asin(sinp);
  }

  // yaw (z-axis rotation)
  const double siny_cosp = 2.0 * (qw * qz + qx * qy);
  const double cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz);
  const double yaw = std::atan2(siny_cosp, cosy_cosp);

  RmEuler e;
  e.rx = static_cast<float>(roll);
  e.ry = static_cast<float>(pitch);
  e.rz = static_cast<float>(yaw);
  return e;
}

bool rm_pose_to_ros_pose(const RmPose & rp, geometry_msgs::msg::Pose & out, std::string & reason)
{
  if (!is_finite(rp.position.x) || !is_finite(rp.position.y) || !is_finite(rp.position.z)) {
    reason = "rm position contains NaN/Inf";
    return false;
  }
  const geometry_msgs::msg::Quaternion q = rm_quat_to_ros(rp.quaternion);
  if (!is_valid_ros_quaternion(q, reason)) {
    if (reason.empty()) {
      reason = "rm quaternion invalid";
    }
    return false;
  }
  out.position.x = rp.position.x;
  out.position.y = rp.position.y;
  out.position.z = rp.position.z;
  out.orientation = q;
  return true;
}

bool ros_pose_to_rm_pose(const geometry_msgs::msg::Pose & pose, RmPose & out, std::string & reason)
{
  if (!is_finite(pose.position.x) || !is_finite(pose.position.y) ||
    !is_finite(pose.position.z))
  {
    reason = "ros position contains NaN/Inf";
    return false;
  }
  if (!is_valid_ros_quaternion(pose.orientation, reason)) {
    return false;
  }
  out.position.x = pose.position.x;
  out.position.y = pose.position.y;
  out.position.z = pose.position.z;
  out.quaternion = ros_quat_to_rm(pose.orientation);
  out.euler = ros_quaternion_to_euler(pose.orientation);
  return true;
}

}  // namespace rm65_dual_arm
