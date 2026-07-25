// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0
//
// 单臂 SDK 封装。本模块是唯一直接 include 厂商 SDK 头文件（rm_service.h）
// 的编译单元，把 rm_robot_handle 的生命周期管理、状态读取、运动执行、急停
// 封装成与纯逻辑层（pose_conversion 等）对接的接口。
//
// 本模块只能在厂商 SDK 头文件到位后编译（CMakeLists 用 rm_service.h 存在性
// 做条件编译）。当 SDK 缺失时，纯逻辑层与测试仍可独立验证。
//
// API 依据（DOCS/01_知识/.../睿尔曼r65四代技术文档/）：
//   - rm_init(rm_thread_mode_e) / rm_destroy() 全局一次
//   - rm_create_robot_arm(const char* ip, int port) -> rm_robot_handle*
//       id>0 成功 / -1 连接失败 / NULL 达到最大连接数 5
//   - rm_delete_robot_arm(rm_robot_handle*) -> int
//   - rm_get_current_arm_state(handle, rm_current_arm_state_t*) -> int
//       结构体含 pose(rm_pose_t) / joint[ARM_DOF] / arm_err(uint) / sys_err(uint)
//   - rm_movel(handle, rm_pose_t, v, r, trajectory_connect, block) -> int
//       v 速度百分比 1..100，block 默认 0（非阻塞）
//   - rm_set_arm_emergency_stop(handle, bool state) -> int
//   - rm_set_arm_stop(handle) -> int   轨迹急停，不可恢复
//
// 错误码（API 返回）：0 成功 / 1 控制器参数错误 / -1 发送失败
//   / -2 接收失败或超时 / -3 解析失败 / -4 到位校验失败 / -5 单线程阻塞超时
//   / -6 规划被停止。控制器错误 arm_err：0x1001 关节通信异常 / 0x1009 超速
//   / 0x100A 超加速度 / 0x100C 拖动超速 / 0x100D 碰撞 / 0x1010 关节掉使能 等。

#ifndef RM65_DUAL_ARM__RM65_ARM_HPP_
#define RM65_DUAL_ARM__RM65_ARM_HPP_

#include <cstdint>
#include <memory>
#include <string>

#include "rm65_dual_arm/pose_conversion.hpp"  // RmPose

// 厂商 SDK 头文件（vendor）。当 SDK 未到位时本头文件不被 CMake 编译。
#include "rm_service.h"

namespace rm65_dual_arm
{

// 单臂快照：供主节点做 delta_guard 基准与 health 发布使用。
struct ArmSnapshot
{
  bool has_pose{false};       // 是否已读到过合法 TCP
  RmPose pose{};              // 当前 TCP（rm_pose_t 镜像）
  bool connected{false};
  bool estop_active{false};
  int32_t sdk_code{0};        // 最近一次 API 返回码
  int32_t controller_err{0};  // arm_err / sys_err（取最近一次非 0）
  std::string reason;         // 人类可读简短原因
};

// 单臂封装。非线程安全——调用方（主节点）需保证对同一实例的访问串行化
// （主节点用专用 timer/subscription 回调线程模型，运动调用在独立线程）。
class Rm65Arm
{
public:
  enum class Side
  {
    Left,
    Right,
  };

  Rm65Arm(Side side, std::string ip, int port, std::string frame_id);
  ~Rm65Arm();

  Rm65Arm(const Rm65Arm &) = delete;
  Rm65Arm & operator=(const Rm65Arm &) = delete;
  Rm65Arm(Rm65Arm &&) = delete;
  Rm65Arm & operator=(Rm65Arm &&) = delete;

  // 全局初始化：rm_init(RM_TRIPLE_MODE_E)。整个进程只应调用一次。
  // 返回 SDK 返回码。已初始化则幂等返回 0。
  static int init_global();

  // 全局销毁：rm_destroy()。进程退出时调用，关闭所有连接。
  static void destroy_global();

  // 连接机械臂。成功后 connected=true。失败时 reason 填入原因。
  // 返回 true 表示成功建立连接。
  bool connect();

  // 断开（rm_delete_robot_arm）。幂等。
  void disconnect();

  // 读取当前状态并更新快照。失败时 has_pose 保持上一次值，但 connected 与
  // sdk_code/error 更新。返回最新快照引用。
  const ArmSnapshot & update_state();

  // 下发一个目标位姿（rm_movel）。pose 必须已通过上层闸门校验。
  // speed_percent ∈ [1,100]，blend_radius_percent ∈ [0,100]。
  // block=false 默认非阻塞（契约 block=false）。
  // 返回 SDK 返回码；失败时快照的 sdk_code/reason 同步更新。
  int movel(const RmPose & target, int speed_percent, int blend_radius_percent, bool block);

  // 急停（rm_set_arm_emergency_stop）。state=true 急停，false 恢复。
  // 同步更新 estop_active。返回 SDK 返回码。
  int set_emergency_stop(bool state);

  // 轨迹急停（rm_set_arm_stop，不可恢复）。仅用于硬急停路径。
  int hard_stop();

  const ArmSnapshot & snapshot() const { return snapshot_; }
  bool is_connected() const { return snapshot_.connected; }
  const std::string & ip() const { return ip_; }
  const std::string & frame_id() const { return frame_id_; }
  Side side() const { return side_; }

private:
  // 把 SDK 的 rm_current_arm_state_t 拷到 RmPose 镜像。
  // 返回 false 表示位姿非法（NaN/Inf/四元数异常），不更新 snapshot_.pose。
  bool fill_pose_from_state(const rm_current_arm_state_t & state, RmPose & out);

  Side side_;
  std::string ip_;
  int port_;
  std::string frame_id_;
  rm_robot_handle * handle_{nullptr};
  ArmSnapshot snapshot_;
};

}  // namespace rm65_dual_arm

#endif  // RM65_DUAL_ARM__RM65_ARM_HPP_
