// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0

#include <gtest/gtest.h>

#include <cmath>
#include <limits>

#include "rm65_dual_arm/target_validator.hpp"

using rm65_dual_arm::validate_target;

namespace
{
geometry_msgs::msg::PoseStamped make_target(
  const std::string & frame_id, double stamp_sec,
  double x, double y, double z,
  double qx = 0.0, double qy = 0.0, double qz = 0.0, double qw = 1.0)
{
  geometry_msgs::msg::PoseStamped msg;
  msg.header.frame_id = frame_id;
  const double whole = std::floor(stamp_sec);
  msg.header.stamp.sec = static_cast<int32_t>(whole);
  msg.header.stamp.nanosec = static_cast<uint32_t>((stamp_sec - whole) * 1e9);
  msg.pose.position.x = x;
  msg.pose.position.y = y;
  msg.pose.position.z = z;
  msg.pose.orientation.x = qx;
  msg.pose.orientation.y = qy;
  msg.pose.orientation.z = qz;
  msg.pose.orientation.w = qw;
  return msg;
}
}  // namespace

TEST(ValidateTarget, ValidLeftArm)
{
  auto t = make_target("left_arm_base", 10.0, 0.3, 0.0, 0.3);
  auto res = validate_target(t, "left_arm_base", 10.2, 0.5);
  EXPECT_TRUE(res.ok);
  EXPECT_TRUE(res.reason_code.empty());
}

TEST(ValidateTarget, FrameMismatchLeftVsRight)
{
  // 期望左臂 frame，但消息带 right_arm_base
  auto t = make_target("right_arm_base", 10.0, 0.3, 0.0, 0.3);
  auto res = validate_target(t, "left_arm_base", 10.1, 0.5);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "FRAME_MISMATCH");
}

TEST(ValidateTarget, FrameMismatchEmpty)
{
  auto t = make_target("", 10.0, 0.3, 0.0, 0.3);
  auto res = validate_target(t, "left_arm_base", 10.1, 0.5);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "FRAME_MISMATCH");
}

TEST(ValidateTarget, StaleRejected)
{
  // stamp 在 10s，now 在 11s，stale 阈值 0.5s
  auto t = make_target("left_arm_base", 10.0, 0.3, 0.0, 0.3);
  auto res = validate_target(t, "left_arm_base", 11.0, 0.5);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "TARGET_STALE");
}

TEST(ValidateTarget, JustWithinStaleWindow)
{
  // age = 0.5 恰好等于阈值，不超限（用 >，等于通过）
  auto t = make_target("left_arm_base", 10.0, 0.3, 0.0, 0.3);
  auto res = validate_target(t, "left_arm_base", 10.5, 0.5);
  EXPECT_TRUE(res.ok);
}

TEST(ValidateTarget, UnstampedRejected)
{
  // stamp 全 0
  auto t = make_target("left_arm_base", 0.0, 0.3, 0.0, 0.3);
  auto res = validate_target(t, "left_arm_base", 10.0, 0.5);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "TARGET_UNSTAMPED");
}

TEST(ValidateTarget, NaNEositionRejected)
{
  auto t = make_target("left_arm_base", 10.0,
                       std::numeric_limits<double>::quiet_NaN(), 0.0, 0.3);
  auto res = validate_target(t, "left_arm_base", 10.1, 0.5);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "POSE_NON_FINITE");
}

TEST(ValidateTarget, InfPositionRejected)
{
  auto t = make_target("left_arm_base", 10.0,
                       0.0, std::numeric_limits<double>::infinity(), 0.3);
  auto res = validate_target(t, "left_arm_base", 10.1, 0.5);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "POSE_NON_FINITE");
}

TEST(ValidateTarget, NearZeroQuaternionRejected)
{
  auto t = make_target("left_arm_base", 10.0, 0.3, 0.0, 0.3, 0, 0, 0, 0);
  auto res = validate_target(t, "left_arm_base", 10.1, 0.5);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "QUATERNION_BAD");
}

TEST(ValidateTarget, NaNQuaternionRejected)
{
  auto t = make_target("left_arm_base", 10.0, 0.3, 0.0, 0.3,
                       std::numeric_limits<double>::quiet_NaN(), 0, 0, 1.0);
  auto res = validate_target(t, "left_arm_base", 10.1, 0.5);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "QUATERNION_BAD");
}

TEST(ValidateTarget, NonUnitQuaternionRejected)
{
  auto t = make_target("left_arm_base", 10.0, 0.3, 0.0, 0.3, 1.0, 1.0, 1.0, 1.0);
  auto res = validate_target(t, "left_arm_base", 10.1, 0.5);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "QUATERNION_BAD");
}

TEST(ValidateTarget, ClockSkewAbsoluteAge)
{
  // 时钟回拨：now < stamp，但 age 取绝对值，仍应判 stale
  auto t = make_target("left_arm_base", 10.0, 0.3, 0.0, 0.3);
  auto res = validate_target(t, "left_arm_base", 9.0, 0.5);
  EXPECT_FALSE(res.ok);
  EXPECT_EQ(res.reason_code, "TARGET_STALE");
}
