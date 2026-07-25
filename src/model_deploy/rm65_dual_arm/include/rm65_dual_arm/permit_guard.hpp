// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0
//
// 人工安全许可守卫。对齐 act/types/action_publish.py 的 CommandPermit fail-closed
// 设计（绝不 fail-open）：许可无效、stale、异常时一律返回 allowed=false。
//
// 本模块是一个无状态工具类，节点持有其实例，缓存最近一次收到的 CommandPermit
// 消息和接收时间戳。每次目标运动命令下发前调用 resolve() 得到当前有效许可。
//
// reason_code 与 act 侧稳定码对齐：
//   PERMIT_MISSING         启动后从未收到 permit 消息
//   PERMIT_STALE           permit 超过 permit_stale_sec 未更新
//   PERMIT_DENIED          permit 明确 allowed=false，透传上游 reason_code
//   PERMIT_SOURCE_ERROR    permit 字段自相矛盾（allowed=true 但带 reason_code 等）
//
// 注意：CommandPermit 消息本身不带时间戳（对齐 Python dataclass），stale 判断
// 用本节点接收到该消息的本地单调时钟。

#ifndef RM65_DUAL_ARM__PERMIT_GUARD_HPP_
#define RM65_DUAL_ARM__PERMIT_GUARD_HPP_

#include <mutex>
#include <string>

#include "act_interfaces/msg/command_permit.hpp"

namespace rm65_dual_arm
{

// 校验 CommandPermit 字段是否自洽（对齐 Python dataclass 不变量）：
//   allowed=true  -> reason_code 必须为空
//   allowed=false -> reason_code 必须为非空稳定 code
// 不自洽返回 false（视为 PERMIT_SOURCE_ERROR，fail-closed）。
bool is_permit_well_formed(const act_interfaces::msg::CommandPermit & permit);

// 许可解析结果。
struct PermitResult
{
  bool allowed{false};
  std::string reason_code;  // 见上文 reason_code 表
  std::string reason;       // 人类可读
};

// 线程安全的许可缓存。节点订阅 /act/command/permit 后调用 update()，每条
// 目标命令下发前调用 resolve()。
class PermitGuard
{
public:
  PermitGuard() = default;

  // 用收到的 permit 消息与接收时刻（单调时钟秒）更新缓存。
  void update(const act_interfaces::msg::CommandPermit & permit, double now_sec);

  // 解析当前有效许可。若从未收到（!has_message_）-> PERMIT_MISSING；
  // 若 stale -> PERMIT_STALE；若字段不自洽 -> PERMIT_SOURCE_ERROR；
  // 若 allowed=false -> PERMIT_DENIED（透传上游 reason_code）；否则 allowed=true。
  PermitResult resolve(double now_sec, double permit_stale_sec) const;

private:
  mutable std::mutex mutex_;
  bool has_message_{false};
  act_interfaces::msg::CommandPermit last_;
  double last_recv_sec_{0.0};
};

}  // namespace rm65_dual_arm

#endif  // RM65_DUAL_ARM__PERMIT_GUARD_HPP_
