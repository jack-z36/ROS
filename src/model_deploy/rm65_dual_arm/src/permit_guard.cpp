// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0

#include "rm65_dual_arm/permit_guard.hpp"

#include <cmath>

namespace rm65_dual_arm
{

bool is_permit_well_formed(const act_interfaces::msg::CommandPermit & permit)
{
  if (permit.allowed) {
    // allowed=true 时 reason_code 必须为空
    return permit.reason_code.empty();
  }
  // allowed=false 时 reason_code 必须非空
  return !permit.reason_code.empty();
}

void PermitGuard::update(const act_interfaces::msg::CommandPermit & permit, double now_sec)
{
  std::lock_guard<std::mutex> lk(mutex_);
  last_ = permit;
  last_recv_sec_ = now_sec;
  has_message_ = true;
}

PermitResult PermitGuard::resolve(double now_sec, double permit_stale_sec) const
{
  PermitResult res;
  // fail-closed 默认：除非所有条件满足，否则一律 allowed=false。
  res.allowed = false;

  act_interfaces::msg::CommandPermit snapshot;
  double age = 0.0;
  bool has_msg = false;
  {
    std::lock_guard<std::mutex> lk(mutex_);
    has_msg = has_message_;
    snapshot = last_;
    age = std::abs(now_sec - last_recv_sec_);
  }

  if (!has_msg) {
    res.reason_code = "PERMIT_MISSING";
    res.reason = "no permit message received yet";
    return res;
  }

  // stale 判断优先于内容校验（即便内容合法，过期也视为不可信）
  if (!std::isfinite(age) || age > permit_stale_sec) {
    res.reason_code = "PERMIT_STALE";
    res.reason = std::string("permit age ") + std::to_string(age) +
                 "s exceeds permit_stale_sec " + std::to_string(permit_stale_sec) + "s";
    return res;
  }

  if (!is_permit_well_formed(snapshot)) {
    res.reason_code = "PERMIT_SOURCE_ERROR";
    res.reason = "permit fields inconsistent with invariant";
    return res;
  }

  if (!snapshot.allowed) {
    res.reason_code = snapshot.reason_code.empty() ? std::string("PERMIT_DENIED") :
                     snapshot.reason_code;
    res.reason = std::string("human permit denied: ") + res.reason_code;
    return res;
  }

  res.allowed = true;
  res.reason_code.clear();
  res.reason.clear();
  return res;
}

}  // namespace rm65_dual_arm
