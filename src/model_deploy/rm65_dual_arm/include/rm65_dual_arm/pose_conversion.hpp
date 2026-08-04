// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0
//
// 位姿转换：在睿尔曼 SDK 位姿表示与 ROS geometry_msgs 之间做无歧义转换。
//
// 单位与顺序约定（权威依据：DOCS/01_知识/.../睿尔曼r65四代技术文档/）：
//   - 位置：统一米 (m)。rm_pose_t.position 与 ROS pose.position 都按 m 处理，
//     禁止把 mm 当 m（契约 rm65_driver_node 状态发布契约.md）。
//   - 姿态：ROS 用四元数 geometry_msgs::Quaternion，字段顺序 (x, y, z, w)。
//   - 睿尔曼 rm_quat_t 字段顺序常见 (w, x, y, z)，与 ROS 相反，互转必须重排。
//   - 睿尔曼 rm_euler_t 用弧度 (rad)，顺序按文档常用 [rx, ry, rz] 理解为
//     roll/pitch/yaw (ZYX 内蕴)。
//
// 本模块刻意不 include 任何 rm_*.h 厂商头文件，避免纯逻辑测试对 SDK 产生
// 编译依赖。rm65_arm.cpp 在 SDK 边界把 rm_pose_t/rm_quat_t/rm_euler_t 逐字段
// 拷到本模块的 RmPose/RmQuat/RmEuler 后再调用本模块。

#ifndef RM65_DUAL_ARM__POSE_CONVERSION_HPP_
#define RM65_DUAL_ARM__POSE_CONVERSION_HPP_

#include <string>

#include "geometry_msgs/msg/pose.hpp"
#include "geometry_msgs/msg/quaternion.hpp"

namespace rm65_dual_arm
{

// 镜像睿尔曼 rm_quat_t，字段顺序与厂商文档一致 (w, x, y, z)。
struct RmQuat
{
  float w{1.0F};
  float x{0.0F};
  float y{0.0F};
  float z{0.0F};
};

// 镜像睿尔曼 rm_euler_t，单位 rad，顺序 [rx, ry, rz] = [roll, pitch, yaw]。
struct RmEuler
{
  float rx{0.0F};
  float ry{0.0F};
  float rz{0.0F};
};

// 镜像睿尔曼 rm_position_t，单位 m。
struct RmPosition
{
  float x{0.0F};
  float y{0.0F};
  float z{0.0F};
};

// 镜像睿尔曼 rm_pose_t：位置 + 四元数 + 欧拉角同时存在（与厂商结构体同构）。
// 厂商 API 不同接口可能只填其中一组姿态，调用方按需选用 quaternion 或 euler。
struct RmPose
{
  RmPosition position;
  RmQuat quaternion;
  RmEuler euler;
};

// ---------------------------------------------------------------------------
// 四元数相关
// ---------------------------------------------------------------------------

// 校验 ROS 四元数是否合法：有限且模长接近 1。
// 返回 true 合法；reason 在非法时填入简短原因。
bool is_valid_ros_quaternion(const geometry_msgs::msg::Quaternion & q,
                             std::string & reason,
                             double tol = 1e-3);

// 睿尔曼 rm_quat_t (w,x,y,z) -> ROS Quaternion (x,y,z,w)。纯字段重排。
geometry_msgs::msg::Quaternion rm_quat_to_ros(const RmQuat & rq);

// ROS Quaternion (x,y,z,w) -> 睿尔曼 rm_quat_t (w,x,y,z)。纯字段重排。
// 不校验合法性（调用方自行用 is_valid_ros_quaternion 校验）。
RmQuat ros_quat_to_rm(const geometry_msgs::msg::Quaternion & q);

// ---------------------------------------------------------------------------
// 欧拉角 <-> 四元数
// ---------------------------------------------------------------------------

// 睿尔曼欧拉角 [rx, ry, rz] = [roll, pitch, yaw] (rad, ZYX 内蕴) -> ROS 四元数。
// 公式（与 REP-103 / tf2 一致的 ZYX 内蕴 yaw-pitch-roll 约定）：
//   qx = sin(r/2)cos(p/2)cos(y/2) - cos(r/2)sin(p/2)sin(y/2)
//   qy = cos(r/2)sin(p/2)cos(y/2) + sin(r/2)cos(p/2)sin(y/2)
//   qz = cos(r/2)cos(p/2)sin(y/2) - sin(r/2)sin(p/2)cos(y/2)
//   qw = cos(r/2)cos(p/2)cos(y/2) + sin(r/2)sin(p/2)sin(y/2)
// 其中 r=rx(roll), p=ry(pitch), y=rz(yaw)。
geometry_msgs::msg::Quaternion euler_to_ros_quaternion(double roll, double pitch, double yaw);

// ROS 四元数 -> 睿尔曼欧拉角 [rx, ry, rz] (rad)。是 euler_to_ros_quaternion 的逆运算。
// 输入 q 必须是合法单位四元数（调用方先用 is_valid_ros_quaternion 校验）。
RmEuler ros_quaternion_to_euler(const geometry_msgs::msg::Quaternion & q);

// ---------------------------------------------------------------------------
// 整体位姿转换
// ---------------------------------------------------------------------------

// RmPose（优先用 quaternion）-> ROS Pose。
// 若 quaternion 模长非法（接近 0 / NaN），返回 false 并填 reason；pose 输出未定义。
bool rm_pose_to_ros_pose(const RmPose & rp, geometry_msgs::msg::Pose & out, std::string & reason);

// ROS Pose -> RmPose。位置直接拷贝；姿态同时填 quaternion 和 euler（由 q 计算）。
// 若 ROS 四元数非法，返回 false 并填 reason；RmPose 输出未定义。
bool ros_pose_to_rm_pose(const geometry_msgs::msg::Pose & pose, RmPose & out, std::string & reason);

}  // namespace rm65_dual_arm

#endif  // RM65_DUAL_ARM__POSE_CONVERSION_HPP_
