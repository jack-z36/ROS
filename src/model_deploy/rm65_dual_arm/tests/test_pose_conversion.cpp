// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0

#include <gtest/gtest.h>

#include <cmath>
#include <limits>

#include "rm65_dual_arm/pose_conversion.hpp"

using rm65_dual_arm::RmQuat;
using rm65_dual_arm::RmEuler;
using rm65_dual_arm::RmPose;
using rm65_dual_arm::euler_to_ros_quaternion;
using rm65_dual_arm::is_valid_ros_quaternion;
using rm65_dual_arm::rm_pose_to_ros_pose;
using rm65_dual_arm::rm_quat_to_ros;
using rm65_dual_arm::ros_pose_to_rm_pose;
using rm65_dual_arm::ros_quat_to_rm;
using rm65_dual_arm::ros_quaternion_to_euler;

namespace
{
constexpr double kPi = 3.14159265358979323846;
constexpr double kTol = 1e-6;

bool quat_eq(const geometry_msgs::msg::Quaternion & a, double x, double y, double z, double w)
{
  return std::abs(a.x - x) < kTol &&
         std::abs(a.y - y) < kTol &&
         std::abs(a.z - z) < kTol &&
         std::abs(a.w - w) < kTol;
}
}  // namespace

// ---------------- quaternion 顺序重排 ----------------

TEST(RmQuatToRos, WxyzToXyzw)
{
  // 睿尔曼 (w=1, x=2, y=3, z=4) -> ROS (x=2, y=3, z=4, w=1)
  RmQuat rq{1.0F, 2.0F, 3.0F, 4.0F};
  auto ros = rm_quat_to_ros(rq);
  EXPECT_TRUE(quat_eq(ros, 2.0, 3.0, 4.0, 1.0));
}

TEST(RosQuatToRm, XyzwToWxyz)
{
  geometry_msgs::msg::Quaternion q;
  q.x = 2.0; q.y = 3.0; q.z = 4.0; q.w = 1.0;
  auto rq = ros_quat_to_rm(q);
  EXPECT_FLOAT_EQ(rq.w, 1.0);
  EXPECT_FLOAT_EQ(rq.x, 2.0);
  EXPECT_FLOAT_EQ(rq.y, 3.0);
  EXPECT_FLOAT_EQ(rq.z, 4.0);
}

TEST(RmRosRoundTrip, QuaternionReorderIsInvolutive)
{
  RmQuat rq{0.5F, 0.5F, 0.5F, 0.5F};
  auto rq2 = ros_quat_to_rm(rm_quat_to_ros(rq));
  EXPECT_FLOAT_EQ(rq.w, rq2.w);
  EXPECT_FLOAT_EQ(rq.x, rq2.x);
  EXPECT_FLOAT_EQ(rq.y, rq2.y);
  EXPECT_FLOAT_EQ(rq.z, rq2.z);
}

// ---------------- 四元数合法性校验 ----------------

TEST(IsValidQuaternion, UnitQuaternionPasses)
{
  geometry_msgs::msg::Quaternion q;
  q.x = 0.0; q.y = 0.0; q.z = 0.0; q.w = 1.0;
  std::string reason;
  EXPECT_TRUE(is_valid_ros_quaternion(q, reason));
  EXPECT_TRUE(reason.empty());
}

TEST(IsValidQuaternion, NearZeroNormRejected)
{
  geometry_msgs::msg::Quaternion q;
  q.x = 0.0; q.y = 0.0; q.z = 0.0; q.w = 0.0;
  std::string reason;
  EXPECT_FALSE(is_valid_ros_quaternion(q, reason));
  EXPECT_FALSE(reason.empty());
}

TEST(IsValidQuaternion, NaNRejected)
{
  geometry_msgs::msg::Quaternion q;
  q.x = std::numeric_limits<double>::quiet_NaN();
  q.y = 0.0; q.z = 0.0; q.w = 1.0;
  std::string reason;
  EXPECT_FALSE(is_valid_ros_quaternion(q, reason));
}

TEST(IsValidQuaternion, InfRejected)
{
  geometry_msgs::msg::Quaternion q;
  q.x = std::numeric_limits<double>::infinity();
  q.y = 0.0; q.z = 0.0; q.w = 1.0;
  std::string reason;
  EXPECT_FALSE(is_valid_ros_quaternion(q, reason));
}

TEST(IsValidQuaternion, NonUnitNormRejected)
{
  geometry_msgs::msg::Quaternion q;
  // 模长 = sqrt(4) = 2，明显非单位
  q.x = 1.0; q.y = 1.0; q.z = 1.0; q.w = 1.0;
  std::string reason;
  EXPECT_FALSE(is_valid_ros_quaternion(q, reason));
}

// ---------------- 欧拉角 <-> 四元数 往返 ----------------

TEST(EulerQuatRoundTrip, Identity)
{
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.0);
  EXPECT_TRUE(quat_eq(q, 0.0, 0.0, 0.0, 1.0));
  auto e = ros_quaternion_to_euler(q);
  EXPECT_NEAR(e.rx, 0.0, kTol);
  EXPECT_NEAR(e.ry, 0.0, kTol);
  EXPECT_NEAR(e.rz, 0.0, kTol);
}

TEST(EulerQuatRoundTrip, PureYaw90)
{
  // 绕 Z 轴 90 度
  auto q = euler_to_ros_quaternion(0.0, 0.0, kPi / 2.0);
  EXPECT_NEAR(q.w, std::cos(kPi / 4.0), kTol);
  EXPECT_NEAR(q.z, std::sin(kPi / 4.0), kTol);
  EXPECT_NEAR(q.x, 0.0, kTol);
  EXPECT_NEAR(q.y, 0.0, kTol);
  auto e = ros_quaternion_to_euler(q);
  EXPECT_NEAR(static_cast<double>(e.rx), 0.0, kTol);
  EXPECT_NEAR(static_cast<double>(e.ry), 0.0, kTol);
  EXPECT_NEAR(static_cast<double>(e.rz), kPi / 2.0, kTol);
}

TEST(EulerQuatRoundTrip, CompositeAngles)
{
  const double roll = 0.3;
  const double pitch = -0.2;
  const double yaw = 0.5;
  auto q = euler_to_ros_quaternion(roll, pitch, yaw);
  auto e = ros_quaternion_to_euler(q);
  EXPECT_NEAR(static_cast<double>(e.rx), roll, kTol);
  EXPECT_NEAR(static_cast<double>(e.ry), pitch, kTol);
  EXPECT_NEAR(static_cast<double>(e.rz), yaw, kTol);
}

TEST(EulerQuatRoundTrip, NegativeAngles)
{
  const double roll = -1.0;
  const double pitch = 0.4;
  const double yaw = -0.7;
  auto q = euler_to_ros_quaternion(roll, pitch, yaw);
  auto e = ros_quaternion_to_euler(q);
  EXPECT_NEAR(static_cast<double>(e.rx), roll, kTol);
  EXPECT_NEAR(static_cast<double>(e.ry), pitch, kTol);
  EXPECT_NEAR(static_cast<double>(e.rz), yaw, kTol);
}

// ---------------- 整体位姿转换 ----------------

TEST(RmPoseToRos, Valid)
{
  RmPose rp;
  rp.position = {0.3F, -0.2F, 0.5F};
  rp.quaternion = {1.0F, 0.0F, 0.0F, 0.0F};  // w,x,y,z
  geometry_msgs::msg::Pose out;
  std::string reason;
  ASSERT_TRUE(rm_pose_to_ros_pose(rp, out, reason));
  EXPECT_FLOAT_EQ(out.position.x, 0.3F);
  EXPECT_FLOAT_EQ(out.position.y, -0.2F);
  EXPECT_FLOAT_EQ(out.position.z, 0.5F);
  // ROS xyzw <- 睿尔曼 wxyz(1,0,0,0) = (0,0,0,1)
  EXPECT_FLOAT_EQ(out.orientation.w, 1.0);
  EXPECT_FLOAT_EQ(out.orientation.x, 0.0);
  EXPECT_FLOAT_EQ(out.orientation.y, 0.0);
  EXPECT_FLOAT_EQ(out.orientation.z, 0.0);
}

TEST(RmPoseToRos, BadQuaternionRejected)
{
  RmPose rp;
  rp.position = {0.0F, 0.0F, 0.0F};
  rp.quaternion = {0.0F, 0.0F, 0.0F, 0.0F};  // 模长 0
  geometry_msgs::msg::Pose out;
  std::string reason;
  EXPECT_FALSE(rm_pose_to_ros_pose(rp, out, reason));
  EXPECT_FALSE(reason.empty());
}

TEST(RmPoseToRos, NaNEositionRejected)
{
  RmPose rp;
  rp.position = {std::numeric_limits<float>::quiet_NaN(), 0.0F, 0.0F};
  rp.quaternion = {1.0F, 0.0F, 0.0F, 0.0F};
  geometry_msgs::msg::Pose out;
  std::string reason;
  EXPECT_FALSE(rm_pose_to_ros_pose(rp, out, reason));
}

TEST(RosPoseToRm, ValidFillsBothQuatAndEuler)
{
  geometry_msgs::msg::Pose p;
  p.position.x = 0.1; p.position.y = 0.2; p.position.z = 0.3;
  p.orientation = euler_to_ros_quaternion(0.0, 0.0, kPi / 2.0);
  RmPose out;
  std::string reason;
  ASSERT_TRUE(ros_pose_to_rm_pose(p, out, reason));
  EXPECT_FLOAT_EQ(out.position.x, 0.1F);
  EXPECT_FLOAT_EQ(out.position.y, 0.2F);
  EXPECT_FLOAT_EQ(out.position.z, 0.3F);
  // euler 的 rz 应约为 pi/2
  EXPECT_NEAR(static_cast<double>(out.euler.rz), kPi / 2.0, kTol);
}

TEST(RosPoseToRm, BadQuaternionRejected)
{
  geometry_msgs::msg::Pose p;
  p.position.x = 0.0; p.position.y = 0.0; p.position.z = 0.0;
  p.orientation.x = 2.0;  // 非单位
  p.orientation.w = 0.0;
  RmPose out;
  std::string reason;
  EXPECT_FALSE(ros_pose_to_rm_pose(p, out, reason));
}
