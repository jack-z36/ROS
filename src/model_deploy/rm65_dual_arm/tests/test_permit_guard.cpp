// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0
//
// permit_guard 测试。重点验证 fail-closed：任何异常/缺失/stale/明确拒绝
// 都必须返回 allowed=false，绝不 fail-open。

#include <gtest/gtest.h>

#include "rm65_dual_arm/permit_guard.hpp"

using rm65_dual_arm::is_permit_well_formed;
using rm65_dual_arm::PermitGuard;
using rm65_dual_arm::PermitResult;

namespace
{
act_interfaces::msg::CommandPermit make_permit(bool allowed, const std::string & reason = "")
{
  act_interfaces::msg::CommandPermit p;
  p.allowed = allowed;
  p.reason_code = reason;
  return p;
}
}  // namespace

// ---------------- 字段自洽校验 ----------------

TEST(PermitWellFormed, AllowedTrueNoReason)
{
  EXPECT_TRUE(is_permit_well_formed(make_permit(true, "")));
}

TEST(PermitWellFormed, AllowedTrueWithReasonRejected)
{
  // 不变量：allowed=true 时 reason_code 必须为空
  EXPECT_FALSE(is_permit_well_formed(make_permit(true, "WHATEVER")));
}

TEST(PermitWellFormed, AllowedFalseWithReason)
{
  EXPECT_TRUE(is_permit_well_formed(make_permit(false, "ESTOP_ACTIVE")));
}

TEST(PermitWellFormed, AllowedFalseNoReasonRejected)
{
  // 不变量：allowed=false 时 reason_code 必须非空
  EXPECT_FALSE(is_permit_well_formed(make_permit(false, "")));
}

// ---------------- PermitGuard::resolve ----------------

TEST(PermitGuard, MissingMessageFailsClosed)
{
  PermitGuard g;
  auto res = g.resolve(/*now*/ 1.0, /*stale*/ 1.0);
  EXPECT_FALSE(res.allowed);
  EXPECT_EQ(res.reason_code, "PERMIT_MISSING");
}

TEST(PermitGuard, AllowedTruePermits)
{
  PermitGuard g;
  g.update(make_permit(true, ""), /*now*/ 10.0);
  auto res = g.resolve(/*now*/ 10.5, /*stale*/ 1.0);
  EXPECT_TRUE(res.allowed) << res.reason;
}

TEST(PermitGuard, AllowedFalseDeniesAndPropagatesReasonCode)
{
  PermitGuard g;
  g.update(make_permit(false, "ESTOP_ACTIVE"), /*now*/ 10.0);
  auto res = g.resolve(/*now*/ 10.5, /*stale*/ 1.0);
  EXPECT_FALSE(res.allowed);
  EXPECT_EQ(res.reason_code, "ESTOP_ACTIVE");
}

TEST(PermitGuard, StaleFailsClosed)
{
  PermitGuard g;
  g.update(make_permit(true, ""), /*now*/ 10.0);
  // 距离上次 2s，超过 stale 阈值 1s
  auto res = g.resolve(/*now*/ 12.0, /*stale*/ 1.0);
  EXPECT_FALSE(res.allowed);
  EXPECT_EQ(res.reason_code, "PERMIT_STALE");
}

TEST(PermitGuard, JustWithinStalePasses)
{
  PermitGuard g;
  g.update(make_permit(true, ""), /*now*/ 10.0);
  // age = 1.0 恰等于阈值（用 >，等于不超限）-> 通过
  auto res = g.resolve(/*now*/ 11.0, /*stale*/ 1.0);
  EXPECT_TRUE(res.allowed) << res.reason;
}

TEST(PermitGuard, InconsistentFieldsFailsClosed)
{
  PermitGuard g;
  // allowed=true 但带 reason_code，违反不变量 -> PERMIT_SOURCE_ERROR
  g.update(make_permit(true, "BOGUS"), /*now*/ 10.0);
  auto res = g.resolve(/*now*/ 10.5, /*stale*/ 1.0);
  EXPECT_FALSE(res.allowed);
  EXPECT_EQ(res.reason_code, "PERMIT_SOURCE_ERROR");
}

TEST(PermitGuard, AllowedFalseEmptyReasonTreatedAsSourceError)
{
  PermitGuard g;
  // allowed=false 但 reason_code 空，违反不变量 -> 源错误，而不是 PERMIT_DENIED
  g.update(make_permit(false, ""), /*now*/ 10.0);
  auto res = g.resolve(/*now*/ 10.5, /*stale*/ 1.0);
  EXPECT_FALSE(res.allowed);
  EXPECT_EQ(res.reason_code, "PERMIT_SOURCE_ERROR");
}

TEST(PermitGuard, LatestUpdateWins)
{
  PermitGuard g;
  g.update(make_permit(false, "ESTOP_ACTIVE"), /*now*/ 10.0);
  g.update(make_permit(true, ""), /*now*/ 10.5);
  auto res = g.resolve(/*now*/ 10.6, /*stale*/ 1.0);
  EXPECT_TRUE(res.allowed) << res.reason;
}

TEST(PermitGuard, DeniedThenStaleStillStale)
{
  PermitGuard g;
  g.update(make_permit(false, "ESTOP_ACTIVE"), /*now*/ 10.0);
  // 即便内容是 denied，stale 判断优先（过期消息不可信）
  auto res = g.resolve(/*now*/ 20.0, /*stale*/ 1.0);
  EXPECT_FALSE(res.allowed);
  EXPECT_EQ(res.reason_code, "PERMIT_STALE");
}
