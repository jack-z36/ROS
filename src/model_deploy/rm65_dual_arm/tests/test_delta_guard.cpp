// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0
//
// delta_guard 是本节点最核心的安全闸门，测试覆盖必须严格。
// 设计原则：宁可误拒，不可误放（false positive 优于 false negative）。

#include <gtest/gtest.h>

#include <cmath>
#include <limits>

#include "rm65_dual_arm/delta_guard.hpp"
#include "rm65_dual_arm/pose_conversion.hpp"

using rm65_dual_arm::check_delta;
using rm65_dual_arm::compute_pose_delta;
using rm65_dual_arm::euler_to_ros_quaternion;
using rm65_dual_arm::RmPose;

namespace
{
constexpr double kPi = 3.14159265358979323846;
constexpr double kTol = 1e-6;

// 默认闸门上限（与 config 一致）
constexpr double kMaxStepXyz = 0.010;     // 1cm
constexpr double kMaxStepAngle = 0.05;    // ~2.9°

geometry_msgs::msg::Pose make_pose(double x, double y, double z,
                                   const geometry_msgs::msg::Quaternion & q)
{
  geometry_msgs::msg::Pose p;
  p.position.x = x; p.position.y = y; p.position.z = z;
  p.orientation = q;
  return p;
}

RmPose make_rm_pose(double x, double y, double z,
                    double qw, double qx, double qy, double qz)
{
  RmPose rp;
  rp.position.x = static_cast<float>(x);
  rp.position.y = static_cast<float>(y);
  rp.position.z = static_cast<float>(z);
  // 睿尔曼 (w,x,y,z)
  rp.quaternion.w = static_cast<float>(qw);
  rp.quaternion.x = static_cast<float>(qx);
  rp.quaternion.y = static_cast<float>(qy);
  rp.quaternion.z = static_cast<float>(qz);
  return rp;
}
}  // namespace

// ---------------- compute_pose_delta 基础测试 ----------------

TEST(ComputeDelta, ZeroDeltaWhenIdentical)
{
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.0);
  auto a = make_pose(0.3, 0.0, 0.3, q);
  double xyz = -1.0, ang = -1.0;
  std::string reason;
  ASSERT_TRUE(compute_pose_delta(a, a, xyz, ang, reason));
  EXPECT_NEAR(xyz, 0.0, kTol);
  EXPECT_NEAR(ang, 0.0, kTol);
}

TEST(ComputeDelta, PureTranslation5mm)
{
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.0);
  auto a = make_pose(0.300, 0.0, 0.3, q);
  auto b = make_pose(0.305, 0.0, 0.3, q);
  double xyz = -1.0, ang = -1.0;
  std::string reason;
  ASSERT_TRUE(compute_pose_delta(a, b, xyz, ang, reason));
  EXPECT_NEAR(xyz, 0.005, kTol);
  EXPECT_NEAR(ang, 0.0, kTol);
}

TEST(ComputeDelta, PureRotationMatchesAngle)
{
  auto q0 = euler_to_ros_quaternion(0.0, 0.0, 0.0);
  auto q1 = euler_to_ros_quaternion(0.0, 0.0, 0.1);  // yaw 0.1rad
  auto a = make_pose(0.3, 0.0, 0.3, q0);
  auto b = make_pose(0.3, 0.0, 0.3, q1);
  double xyz = -1.0, ang = -1.0;
  std::string reason;
  ASSERT_TRUE(compute_pose_delta(a, b, xyz, ang, reason));
  EXPECT_NEAR(xyz, 0.0, kTol);
  EXPECT_NEAR(ang, 0.1, kTol);
}

// ---------------- check_delta：通过路径 ----------------

TEST(CheckDelta, StepHalfCentimeterPasses)
{
  // 当前 TCP，姿态单位四元数
  RmPose cur = make_rm_pose(0.300, 0.0, 0.3, 1.0, 0.0, 0.0, 0.0);
  // 目标位移 0.5cm，姿态不变
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.0);
  auto target = make_pose(0.305, 0.0, 0.3, q);
  auto res = check_delta(true, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_TRUE(res.ok) << res.reason;
  EXPECT_NEAR(res.xyz_m, 0.005, kTol);
}

TEST(CheckDelta, StepExactlyAtLimitPasses)
{
  // 1cm 恰好等于上限，用 >，不超限 -> 通过
  RmPose cur = make_rm_pose(0.300, 0.0, 0.3, 1.0, 0.0, 0.0, 0.0);
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.0);
  auto target = make_pose(0.310, 0.0, 0.3, q);
  auto res = check_delta(true, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_TRUE(res.ok) << res.reason;
}

TEST(CheckDelta, SmallAngleRotationPasses)
{
  RmPose cur = make_rm_pose(0.3, 0.0, 0.3, 1.0, 0.0, 0.0, 0.0);
  // 0.05rad 恰等于上限 -> 通过
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.05);
  auto target = make_pose(0.3, 0.0, 0.3, q);
  auto res = check_delta(true, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_TRUE(res.ok) << res.reason;
}

// ---------------- check_delta：拒绝路径（核心安全）----------------

TEST(CheckDelta, StepTwoCentimeterRejected)
{
  // 2cm 超过 1cm 上限 -> 必须拒绝
  RmPose cur = make_rm_pose(0.300, 0.0, 0.3, 1.0, 0.0, 0.0, 0.0);
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.0);
  auto target = make_pose(0.320, 0.0, 0.3, q);
  auto res = check_delta(true, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "DELTA_EXCEEDED");
  EXPECT_GT(res.xyz_m, kMaxStepXyz);
}

TEST(CheckDelta, LargeTranslationRejected)
{
  // 0.3m 位移，明显大运动 -> 必须拒绝
  RmPose cur = make_rm_pose(0.000, 0.0, 0.3, 1.0, 0.0, 0.0, 0.0);
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.0);
  auto target = make_pose(0.300, 0.0, 0.3, q);
  auto res = check_delta(true, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "DELTA_EXCEEDED");
}

TEST(CheckDelta, AngleFiveDegreesRejected)
{
  // 5° = 0.0873rad 超过 ~2.9°=0.05rad 上限 -> 拒绝
  RmPose cur = make_rm_pose(0.3, 0.0, 0.3, 1.0, 0.0, 0.0, 0.0);
  auto q = euler_to_ros_quaternion(0.0, 0.0, 5.0 * kPi / 180.0);
  auto target = make_pose(0.3, 0.0, 0.3, q);
  auto res = check_delta(true, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "DELTA_EXCEEDED");
}

TEST(CheckDelta, LargeRotationNinetyDegreesRejected)
{
  RmPose cur = make_rm_pose(0.3, 0.0, 0.3, 1.0, 0.0, 0.0, 0.0);
  auto q = euler_to_ros_quaternion(0.0, 0.0, kPi / 2.0);  // 90°
  auto target = make_pose(0.3, 0.0, 0.3, q);
  auto res = check_delta(true, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "DELTA_EXCEEDED");
}

// ---------------- check_delta：当前 TCP 异常 ----------------

TEST(CheckDelta, MissingCurrentRejected)
{
  // 首次未读到真实 TCP -> 拒绝（不假设零位）
  RmPose cur{};  // has_current=false 时 cur 不被使用
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.0);
  auto target = make_pose(0.305, 0.0, 0.3, q);
  auto res = check_delta(false, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "CURRENT_MISSING");
}

TEST(CheckDelta, NaNCurrentRejected)
{
  RmPose cur = make_rm_pose(
    std::numeric_limits<double>::quiet_NaN(), 0.0, 0.3, 1.0, 0.0, 0.0, 0.0);
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.0);
  auto target = make_pose(0.305, 0.0, 0.3, q);
  auto res = check_delta(true, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_FALSE(res.ok);
  // 当前 TCP NaN 会被 rm_pose_to_ros_pose 在位置检查里拒绝
  EXPECT_TRUE(res.reason_code == "CURRENT_QUATERNION_BAD" ||
              res.reason_code == "CURRENT_NON_FINITE")
    << "got: " << res.reason_code;
}

TEST(CheckDelta, BadCurrentQuaternionRejected)
{
  // 当前 TCP 四元数全 0
  RmPose cur = make_rm_pose(0.3, 0.0, 0.3, 0.0, 0.0, 0.0, 0.0);
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.0);
  auto target = make_pose(0.305, 0.0, 0.3, q);
  auto res = check_delta(true, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "CURRENT_QUATERNION_BAD");
}

// ---------------- 边界：组合位移+旋转 ----------------

TEST(CheckDelta, CombinedSmallDeltaPasses)
{
  // 位移 0.8cm（<1cm），旋转 0.04rad（<0.05rad），都未超限 -> 通过
  RmPose cur = make_rm_pose(0.300, 0.0, 0.3, 1.0, 0.0, 0.0, 0.0);
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.04);
  auto target = make_pose(0.308, 0.0, 0.3, q);
  auto res = check_delta(true, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_TRUE(res.ok) << res.reason;
}

TEST(CheckDelta, CombinedOneExceedsRejected)
{
  // 位移 0.8cm（<1cm 通过），但旋转 0.06rad（>0.05 拒绝）-> 整体拒绝
  RmPose cur = make_rm_pose(0.300, 0.0, 0.3, 1.0, 0.0, 0.0, 0.0);
  auto q = euler_to_ros_quaternion(0.0, 0.0, 0.06);
  auto target = make_pose(0.308, 0.0, 0.3, q);
  auto res = check_delta(true, cur, target, kMaxStepXyz, kMaxStepAngle);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "DELTA_EXCEEDED");
}
