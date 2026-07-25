// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0

#include "rm65_dual_arm/rm65_arm.hpp"

#include <cmath>
#include <cstring>
#include <mutex>

#include "rm65_dual_arm/pose_conversion.hpp"

namespace
{
// 全局 SDK 初始化标志（进程级）。rm_init / rm_destroy 必须全局成对调用。
// 用 once_flag 保证只调一次。
std::once_flag g_init_once;
bool g_initialized = false;
}  // namespace

namespace rm65_dual_arm
{

namespace
{
// 单边名，用于日志与 reason。
const char * side_name(Rm65Arm::Side s)
{
  return s == Rm65Arm::Side::Left ? "left" : "right";
}

// 把 SDK 错误码翻译成简短描述（仅用于人类可读 reason，不覆盖稳定 reason_code）。
std::string sdk_code_text(int code)
{
  switch (code) {
    case 0: return "ok";
    case 1: return "controller returned false (param error or arm state error)";
    case -1: return "send failed (link problem)";
    case -2: return "recv failed or controller timeout";
    case -3: return "parse failed";
    case -4: return "arrival check failed";
    case -5: return "single-thread block timeout";
    case -6: return "motion planning stopped";
    default: return std::string("unknown sdk code ") + std::to_string(code);
  }
}
}  // namespace

Rm65Arm::Rm65Arm(Side side, std::string ip, int port, std::string frame_id)
: side_(side), ip_(std::move(ip)), port_(port), frame_id_(std::move(frame_id))
{
  snapshot_.reason = std::string("not connected (") + side_name(side_) + ")";
}

Rm65Arm::~Rm65Arm()
{
  disconnect();
}

int Rm65Arm::init_global()
{
  std::call_once(g_init_once, []() {
    // 三线程模式：含 UDP 监测线程，双臂 UDP 主动上报必需。
    const int ret = rm_init(RM_TRIPLE_MODE_E);
    g_initialized = (ret == 0);
  });
  // call_once 内部已设置 g_initialized；若 rm_init 失败这里返回原码。
  // 注意：因 rm_init 返回值在 lambda 内捕获，这里无法直接返回原始码；
  // 返回 0 表示已完成初始化流程，非 0 通过 g_initialized 状态体现。
  return g_initialized ? 0 : -1;
}

void Rm65Arm::destroy_global()
{
  if (g_initialized) {
    // rm_destroy 关闭所有连接（进程级）。仅进程退出时调用。
    rm_destroy();
    g_initialized = false;
  }
}

bool Rm65Arm::connect()
{
  if (handle_ != nullptr) {
    // 已连接，幂等视为成功
    snapshot_.connected = true;
    return true;
  }
  if (!g_initialized) {
    snapshot_.connected = false;
    snapshot_.sdk_code = -1;
    snapshot_.reason = std::string("SDK not initialized (") + side_name(side_) + ")";
    return false;
  }
  // rm_create_robot_arm(const char* ip, int port) -> rm_robot_handle*
  //   id>0 成功 / -1 连接失败 / NULL 达到最大连接数 5
  rm_robot_handle * h = rm_create_robot_arm(ip_.c_str(), port_);
  if (h == nullptr) {
    snapshot_.connected = false;
    snapshot_.sdk_code = -1;
    snapshot_.reason =
      std::string("create_robot_arm returned NULL (max 5 handles?) for ") + side_name(side_);
    return false;
  }
  if (h->id == -1) {
    // 连接失败，按文档仍需 rm_delete_robot_arm 释放句柄槽
    rm_delete_robot_arm(h);
    snapshot_.connected = false;
    snapshot_.sdk_code = -1;
    snapshot_.reason =
      std::string("connect failed for ") + side_name(side_) + " at " + ip_ + ":" +
      std::to_string(port_);
    return false;
  }
  handle_ = h;
  snapshot_.connected = true;
  snapshot_.sdk_code = 0;
  snapshot_.reason = std::string("connected (") + side_name(side_) + ", id=" +
                    std::to_string(h->id) + ")";
  return true;
}

void Rm65Arm::disconnect()
{
  if (handle_ != nullptr) {
    rm_delete_robot_arm(handle_);
    handle_ = nullptr;
  }
  snapshot_.connected = false;
  snapshot_.has_pose = false;
  snapshot_.reason = std::string("disconnected (") + side_name(side_) + ")";
}

bool Rm65Arm::fill_pose_from_state(const rm_current_arm_state_t & state, RmPose & out)
{
  // SDK 文档：rm_current_arm_state_t.pose 含 position(m) / quaternion(w,x,y,z) / euler(rad)。
  const auto & p = state.pose.position;
  const auto & q = state.pose.quaternion;
  if (!std::isfinite(p.x) || !std::isfinite(p.y) || !std::isfinite(p.z)) {
    return false;
  }
  RmQuat rq{q.w, q.x, q.y, q.z};  // 睿尔曼 (w,x,y,z)
  // 借用 pose_conversion 的合法性校验：先转 ROS 四元数再校验模长
  geometry_msgs::msg::Quaternion ros_q = rm_quat_to_ros(rq);
  std::string reason;
  if (!is_valid_ros_quaternion(ros_q, reason)) {
    return false;
  }
  out.position = {p.x, p.y, p.z};
  out.quaternion = rq;
  // euler 直接拷贝（SDK 已提供，避免重复三角运算）
  out.euler = {state.pose.euler.rx, state.pose.euler.ry, state.pose.euler.rz};
  return true;
}

const ArmSnapshot & Rm65Arm::update_state()
{
  if (handle_ == nullptr) {
    snapshot_.connected = false;
    snapshot_.sdk_code = -1;
    if (snapshot_.reason.empty() || snapshot_.reason.rfind("connected", 0) == 0) {
      snapshot_.reason = std::string("no handle (") + side_name(side_) + ")";
    }
    return snapshot_;
  }
  rm_current_arm_state_t state;
  std::memset(&state, 0, sizeof(state));
  const int ret = rm_get_current_arm_state(handle_, &state);
  snapshot_.sdk_code = ret;
  if (ret != 0) {
    // 读状态失败：保留上一次 has_pose（避免抖动），但标记原因
    snapshot_.reason =
      std::string("get_current_arm_state failed (") + side_name(side_) + "): " +
      sdk_code_text(ret);
    // -1/-2 通常意味着链路问题，这里不主动断连（重连由主节点监控层决定）
    return snapshot_;
  }
  // arm_err / sys_err（uint16 文档，取非 0 记录）
  const uint32_t arm_err = state.arm_err;
  const uint32_t sys_err = state.sys_err;
  snapshot_.controller_err = static_cast<int32_t>(arm_err != 0 ? arm_err : sys_err);
  RmPose pose;
  if (fill_pose_from_state(state, pose)) {
    snapshot_.pose = pose;
    snapshot_.has_pose = true;
    snapshot_.reason = std::string("ok (") + side_name(side_) + ")";
  } else {
    // 位姿非法：不覆盖已有合法 pose，避免污染 delta_guard 基准
    snapshot_.reason =
      std::string("invalid pose from arm (") + side_name(side_) + ")";
  }
  return snapshot_;
}

int Rm65Arm::movel(const RmPose & target, int speed_percent, int blend_radius_percent, bool block)
{
  if (handle_ == nullptr) {
    snapshot_.sdk_code = -1;
    snapshot_.reason = std::string("movel without handle (") + side_name(side_) + ")";
    return -1;
  }
  // 构造 SDK rm_pose_t（位置 m / 姿态用 euler rad）。
  // 速度百分比钳到 [1,100]，blend 半径百分比钳到 [0,100]。
  const int v = speed_percent < 1 ? 1 : (speed_percent > 100 ? 100 : speed_percent);
  const int r = blend_radius_percent < 0 ? 0 :
                (blend_radius_percent > 100 ? 100 : blend_radius_percent);
  rm_pose_t sdk_pose;
  std::memset(&sdk_pose, 0, sizeof(sdk_pose));
  sdk_pose.position.x = target.position.x;
  sdk_pose.position.y = target.position.y;
  sdk_pose.position.z = target.position.z;
  sdk_pose.euler.rx = target.euler.rx;
  sdk_pose.euler.ry = target.euler.ry;
  sdk_pose.euler.rz = target.euler.rz;
  // quaternion 也填上（SDK 内部按需选用）
  sdk_pose.quaternion.w = target.quaternion.w;
  sdk_pose.quaternion.x = target.quaternion.x;
  sdk_pose.quaternion.y = target.quaternion.y;
  sdk_pose.quaternion.z = target.quaternion.z;
  // trajectory_connect=0 立即规划；block 按参数。
  const int ret = rm_movel(handle_, sdk_pose, v, r, /*trajectory_connect*/ 0, block ? 1 : 0);
  snapshot_.sdk_code = ret;
  if (ret != 0) {
    snapshot_.reason =
      std::string("rm_movel failed (") + side_name(side_) + "): " + sdk_code_text(ret);
  }
  return ret;
}

int Rm65Arm::set_emergency_stop(bool state)
{
  if (handle_ == nullptr) {
    return -1;
  }
  const int ret = rm_set_arm_emergency_stop(handle_, state);
  snapshot_.sdk_code = ret;
  // 急停状态本地记录（即便返回码非 0，仍按请求意图标记，安全优先）
  snapshot_.estop_active = state;
  if (ret != 0) {
    snapshot_.reason =
      std::string("set_emergency_stop(") + (state ? "true" : "false") + ") failed (" +
      side_name(side_) + "): " + sdk_code_text(ret);
  }
  return ret;
}

int Rm65Arm::hard_stop()
{
  if (handle_ == nullptr) {
    return -1;
  }
  // rm_set_arm_stop：关节最快速度停止，轨迹不可恢复。仅硬急停。
  const int ret = rm_set_arm_stop(handle_);
  snapshot_.sdk_code = ret;
  snapshot_.estop_active = true;
  return ret;
}

}  // namespace rm65_dual_arm
