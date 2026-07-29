// Copyright (c) model_deploy Maintainers
// SPDX-License-Identifier: Apache-2.0

#include "rm65_dual_arm/rm65_dual_arm_node.hpp"

#include <chrono>
#include <stdexcept>
#include <string>

#include "rm65_dual_arm/delta_guard.hpp"
#include "rm65_dual_arm/pose_conversion.hpp"
#include "rm65_dual_arm/target_validator.hpp"

namespace rm65_dual_arm
{

namespace
{
using namespace std::chrono_literals;

double monotonic_now_sec()
{
  return std::chrono::duration<double>(
           std::chrono::steady_clock::now().time_since_epoch()).count();
}

double ros_now_sec(const rclcpp::Node & node)
{
  // rclcpp::Time 没有 sec/nanosec 成员（那是消息 builtin_interfaces/Time 的字段），
  // 用 seconds() 直接拿双精度秒。
  return node.now().seconds();
}

// 把 PoseStamped 的 pose 转成 RmPose（含 euler），供 rm_movel 使用。
// 校验失败返回 false 并填 reason。
bool to_rm_pose_for_movel(const geometry_msgs::msg::PoseStamped & target,
                          RmPose & out,
                          std::string & reason)
{
  return ros_pose_to_rm_pose(target.pose, out, reason);
}
}  // namespace

Rm65DualArmNode::Rm65DualArmNode(const rclcpp::NodeOptions & options)
: rclcpp::Node("rm65_dual_arm_node", options)
{
  config_ = load_and_validate_config();

  // 全局 SDK 初始化（三线程模式，含 UDP 监测）
  if (Rm65Arm::init_global() != 0) {
    throw std::runtime_error("rm_init(RM_TRIPLE_MODE_E) failed");
  }

  // 构造左右臂封装
  left_arm_ = std::make_unique<Rm65Arm>(
    Rm65Arm::Side::Left, config_.left_ip, config_.left_port, config_.left_frame_id);
  right_arm_ = std::make_unique<Rm65Arm>(
    Rm65Arm::Side::Right, config_.right_ip, config_.right_port, config_.right_frame_id);

  // 发布者（TCP pose 发裸 Pose，匹配 ACT 大脑的订阅类型）
  left_pose_pub_ = create_publisher<geometry_msgs::msg::Pose>(
    config_.left_tcp_pose_topic, 10);
  right_pose_pub_ = create_publisher<geometry_msgs::msg::Pose>(
    config_.right_tcp_pose_topic, 10);
  health_pub_ = create_publisher<act_interfaces::msg::HardwareHealth>(
    config_.health_topic, 10);

  // 订阅者
  left_target_sub_ = create_subscription<geometry_msgs::msg::PoseStamped>(
    config_.left_target_topic, 10,
    std::bind(&Rm65DualArmNode::on_left_target, this, std::placeholders::_1));
  right_target_sub_ = create_subscription<geometry_msgs::msg::PoseStamped>(
    config_.right_target_topic, 10,
    std::bind(&Rm65DualArmNode::on_right_target, this, std::placeholders::_1));
  permit_sub_ = create_subscription<act_interfaces::msg::CommandPermit>(
    config_.permit_topic, 10,
    std::bind(&Rm65DualArmNode::on_permit, this, std::placeholders::_1));

  // service
  estop_service_ = create_service<std_srvs::srv::SetBool>(
    config_.emergency_stop_service,
    std::bind(&Rm65DualArmNode::on_emergency_stop, this,
              std::placeholders::_1, std::placeholders::_2));

  // 定时器
  const auto pose_period = std::chrono::microseconds(
    static_cast<int64_t>(1e6 / std::max(config_.pose_hz, 1.0)));
  const auto health_period = std::chrono::microseconds(
    static_cast<int64_t>(1e6 / std::max(config_.health_hz, 1.0)));
  pose_timer_ = create_wall_timer(
    pose_period, std::bind(&Rm65DualArmNode::on_pose_timer, this));
  health_timer_ = create_wall_timer(
    health_period, std::bind(&Rm65DualArmNode::on_health_timer, this));

  RCLCPP_INFO(get_logger(),
    "rm65_dual_arm_node ready: left=%s:%d (%s), right=%s:%d (%s), "
    "speed_percent=%d, max_step_xyz=%.4fm max_step_angle=%.4frad",
    config_.left_ip.c_str(), config_.left_port, config_.left_frame_id.c_str(),
    config_.right_ip.c_str(), config_.right_port, config_.right_frame_id.c_str(),
    config_.speed_percent, config_.max_step_xyz_m, config_.max_step_angle_rad);

  // 尝试首次连接（失败不致命，定时器会持续尝试更新状态；但记录日志）
  if (!left_arm_->connect()) {
    RCLCPP_WARN(get_logger(), "left arm connect failed: %s",
      left_arm_->snapshot().reason.c_str());
  }
  if (!right_arm_->connect()) {
    RCLCPP_WARN(get_logger(), "right arm connect failed: %s",
      right_arm_->snapshot().reason.c_str());
  }
}

Rm65DualArmNode::~Rm65DualArmNode()
{
  // 节点析构时断开两臂（rm_delete_robot_arm）。全局 rm_destroy 留给 main 退出时调用。
  if (left_arm_) {
    left_arm_->disconnect();
  }
  if (right_arm_) {
    right_arm_->disconnect();
  }
}

NodeConfig Rm65DualArmNode::load_and_validate_config()
{
  NodeConfig c;

  // 左右臂
  c.left_ip = declare_parameter<std::string>("left_arm.ip", c.left_ip);
  c.left_port = declare_parameter<int>("left_arm.port", c.left_port);
  c.left_frame_id = declare_parameter<std::string>("left_arm.frame_id", c.left_frame_id);
  c.right_ip = declare_parameter<std::string>("right_arm.ip", c.right_ip);
  c.right_port = declare_parameter<int>("right_arm.port", c.right_port);
  c.right_frame_id = declare_parameter<std::string>("right_arm.frame_id", c.right_frame_id);

  // 运动
  c.speed_percent = declare_parameter<int>("motion.speed_percent", c.speed_percent);
  c.blend_radius_percent = declare_parameter<int>("motion.blend_radius_percent", c.blend_radius_percent);
  c.block = declare_parameter<bool>("motion.block", c.block);
  c.command_timeout_sec = declare_parameter<double>("motion.command_timeout_sec", c.command_timeout_sec);

  // 安全
  c.stale_target_sec = declare_parameter<double>("safety.stale_target_sec", c.stale_target_sec);
  c.permit_stale_sec = declare_parameter<double>("safety.permit_stale_sec", c.permit_stale_sec);
  c.max_step_xyz_m = declare_parameter<double>("safety.max_step_xyz_m", c.max_step_xyz_m);
  c.max_step_angle_rad = declare_parameter<double>("safety.max_step_angle_rad", c.max_step_angle_rad);

  // 发布频率
  c.pose_hz = declare_parameter<double>("publish.pose_hz", c.pose_hz);
  c.health_hz = declare_parameter<double>("publish.health_hz", c.health_hz);

  // topics
  c.left_tcp_pose_topic = declare_parameter<std::string>("topics.left_tcp_pose", c.left_tcp_pose_topic);
  c.right_tcp_pose_topic = declare_parameter<std::string>("topics.right_tcp_pose", c.right_tcp_pose_topic);
  c.health_topic = declare_parameter<std::string>("topics.health", c.health_topic);
  c.left_target_topic = declare_parameter<std::string>("topics.left_target", c.left_target_topic);
  c.right_target_topic = declare_parameter<std::string>("topics.right_target", c.right_target_topic);
  c.permit_topic = declare_parameter<std::string>("topics.permit", c.permit_topic);
  c.emergency_stop_service = declare_parameter<std::string>("topics.emergency_stop_service", c.emergency_stop_service);

  // ---- 启动期硬性校验（失败抛异常，拒绝启动优于静默错配）----
  if (c.left_ip.empty() || c.right_ip.empty()) {
    throw std::runtime_error("left_arm.ip / right_arm.ip must not be empty");
  }
  if (c.left_ip == c.right_ip) {
    throw std::runtime_error("left_arm.ip and right_arm.ip must differ");
  }
  if (c.left_port <= 0 || c.right_port <= 0) {
    throw std::runtime_error("arm port must be positive");
  }
  if (c.speed_percent < 1 || c.speed_percent > 100) {
    throw std::runtime_error("motion.speed_percent must be in [1,100]");
  }
  // ★ delta_guard 启动期硬上限：防止误配成大运动
  if (c.max_step_xyz_m <= 0.0 || c.max_step_xyz_m > kHardMaxStepXyzM) {
    throw std::runtime_error(
      "safety.max_step_xyz_m must be in (0, " + std::to_string(kHardMaxStepXyzM) + "] m");
  }
  if (c.max_step_angle_rad <= 0.0 || c.max_step_angle_rad > kHardMaxStepAngleRad) {
    throw std::runtime_error(
      "safety.max_step_angle_rad must be in (0, " + std::to_string(kHardMaxStepAngleRad) + "] rad");
  }
  if (c.left_frame_id != "left_arm_base" || c.right_frame_id != "right_arm_base") {
    throw std::runtime_error(
      "frame_id must be left_arm_base / right_arm_base respectively");
  }
  if (c.permit_stale_sec <= 0.0 || c.stale_target_sec <= 0.0) {
    throw std::runtime_error("stale thresholds must be positive");
  }

  return c;
}

void Rm65DualArmNode::on_left_target(const geometry_msgs::msg::PoseStamped::SharedPtr msg)
{
  std::lock_guard<std::mutex> lk(left_motion_mutex_);
  const std::string reject = handle_target(Rm65Arm::Side::Left, *msg);
  if (!reject.empty()) {
    RCLCPP_DEBUG(get_logger(), "left target rejected: %s", reject.c_str());
  }
}

void Rm65DualArmNode::on_right_target(const geometry_msgs::msg::PoseStamped::SharedPtr msg)
{
  std::lock_guard<std::mutex> lk(right_motion_mutex_);
  const std::string reject = handle_target(Rm65Arm::Side::Right, *msg);
  if (!reject.empty()) {
    RCLCPP_DEBUG(get_logger(), "right target rejected: %s", reject.c_str());
  }
}

void Rm65DualArmNode::on_permit(const act_interfaces::msg::CommandPermit::SharedPtr msg)
{
  // 用单调时钟做 stale 判断基准（不依赖 ROS 时间，避免仿真时钟回拨）
  permit_guard_.update(*msg, monotonic_now_sec());
}

void Rm65DualArmNode::on_emergency_stop(
  const std::shared_ptr<std_srvs::srv::SetBool::Request> request,
  std::shared_ptr<std_srvs::srv::SetBool::Response> response)
{
  const bool want_stop = request->data;
  RCLCPP_WARN(get_logger(), "emergency_stop service called: %s",
    want_stop ? "STOP" : "RELEASE");
  int left_ret = 0;
  int right_ret = 0;
  {
    std::lock_guard<std::mutex> lk(left_motion_mutex_);
    if (left_arm_) {
      left_ret = left_arm_->set_emergency_stop(want_stop);
    }
  }
  {
    std::lock_guard<std::mutex> lk(right_motion_mutex_);
    if (right_arm_) {
      right_ret = right_arm_->set_emergency_stop(want_stop);
    }
  }
  // 急停意图本地立即生效（即便 SDK 返回非 0，也按 fail-safe 标记）
  estop_active_ = want_stop;
  response->success = (left_ret == 0 && right_ret == 0);
  response->message = std::string("left ret=") + std::to_string(left_ret) +
                      ", right ret=" + std::to_string(right_ret);
}

std::string Rm65DualArmNode::handle_target(Rm65Arm::Side side,
                                           const geometry_msgs::msg::PoseStamped & target)
{
  // 选择对应臂与配置
  Rm65Arm * arm = (side == Rm65Arm::Side::Left) ? left_arm_.get() : right_arm_.get();
  const std::string & expected_frame =
    (side == Rm65Arm::Side::Left) ? config_.left_frame_id : config_.right_frame_id;
  auto & motion_mutex =
    (side == Rm65Arm::Side::Left) ? left_motion_mutex_ : right_motion_mutex_;
  (void)motion_mutex;  // 调用方已加锁

  // 闸门 4：急停激活
  if (estop_active_.load()) {
    return "ESTOP_ACTIVE";
  }

  // 闸门 5：SDK 已连接
  if (!arm || !arm->is_connected()) {
    return "NOT_CONNECTED";
  }

  // 闸门 1：许可（fail-closed）
  const PermitResult permit =
    permit_guard_.resolve(monotonic_now_sec(), config_.permit_stale_sec);
  if (!permit.allowed) {
    return permit.reason_code.empty() ? std::string("PERMIT_DENIED") : permit.reason_code;
  }

  // 闸门 2：目标静态校验（frame_id / finite / quaternion / stale）
  const ValidationResult vres = validate_target(
    target, expected_frame, ros_now_sec(*this), config_.stale_target_sec);
  if (!vres.ok) {
    return vres.reason_code.empty() ? std::string("TARGET_INVALID") : vres.reason_code;
  }

  // 转为 RmPose（含 euler），同时再做一次 quaternion 合法性校验
  RmPose rm_target;
  std::string conv_reason;
  if (!to_rm_pose_for_movel(target, rm_target, conv_reason)) {
    return std::string("TARGET_CONVERT:") + conv_reason;
  }

  // 闸门 3：★ delta_guard 微小运动闸（核心安全）
  const ArmSnapshot & snap = arm->snapshot();
  const DeltaResult dres = check_delta(
    snap.has_pose, snap.pose, target.pose,
    config_.max_step_xyz_m, config_.max_step_angle_rad);
  if (!dres.ok) {
    return dres.reason_code.empty() ? std::string("DELTA_REJECTED") : dres.reason_code;
  }

  // 全部闸门通过，下发 rm_movel
  const int ret = arm->movel(
    rm_target, config_.speed_percent, config_.blend_radius_percent, config_.block);
  if (ret != 0) {
    return std::string("SDK_ERROR:") + std::to_string(ret);
  }
  return std::string();
}

void Rm65DualArmNode::on_pose_timer()
{
  // 更新两侧状态并发布 TCP pose（裸 Pose，无 header；坐标系约定见头文件注释）
  auto publish_pose = [](Rm65Arm * arm,
                         rclcpp::Publisher<geometry_msgs::msg::Pose>::SharedPtr pub) {
      if (!arm) {
        return;
      }
      const ArmSnapshot & snap = arm->update_state();
      if (!snap.has_pose) {
        return;  // 无合法 pose 不发布（契约：不发布伪造 pose）
      }
      geometry_msgs::msg::Pose msg;
      std::string reason;
      if (!rm_pose_to_ros_pose(snap.pose, msg, reason)) {
        // 转换失败说明 pose 非法，跳过本次发布
        return;
      }
      pub->publish(msg);
    };
  publish_pose(left_arm_.get(), left_pose_pub_);
  publish_pose(right_arm_.get(), right_pose_pub_);
}

void Rm65DualArmNode::on_health_timer()
{
  act_interfaces::msg::HardwareHealth hh;
  hh.header.stamp = now();
  hh.header.frame_id = "rm65";

  auto fill = [this](Rm65Arm * arm, bool & connected, bool & estop,
                     int32_t & sdk_code, int32_t & ctrl_err, std::string & reason) {
      if (!arm) {
        connected = false;
        reason = "arm object null";
        return;
      }
      const ArmSnapshot & snap = arm->snapshot();
      connected = snap.connected;
      estop = snap.estop_active || estop_active_.load();
      sdk_code = snap.sdk_code;
      ctrl_err = snap.controller_err;
      reason = snap.reason;
    };

  fill(left_arm_.get(), hh.left_connected, hh.left_estop_active,
       hh.left_sdk_code, hh.left_controller_err, hh.left_reason);
  fill(right_arm_.get(), hh.right_connected, hh.right_estop_active,
       hh.right_sdk_code, hh.right_controller_err, hh.right_reason);

  {
    std::lock_guard<std::mutex> lk(health_mutex_);
    last_health_ = hh;
  }
  health_pub_->publish(hh);
}

}  // namespace rm65_dual_arm

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::NodeOptions options;
  // 允许从参数文件 / 命令行 --params-file 加载，use_intra_process 无需特殊处理
  rclcpp::Logger fallback_logger = rclcpp::get_logger("rm65_dual_arm_node");
  int rc = 0;
  try {
    rclcpp::spin(std::make_shared<rm65_dual_arm::Rm65DualArmNode>(options));
  } catch (const std::exception & e) {
    RCLCPP_FATAL(fallback_logger, "rm65_dual_arm_node failed to start: %s", e.what());
    rc = 1;
  }
  rclcpp::shutdown();
  // 进程退出时全局销毁 SDK（关闭所有连接）
  rm65_dual_arm::Rm65Arm::destroy_global();
  return rc;
}
