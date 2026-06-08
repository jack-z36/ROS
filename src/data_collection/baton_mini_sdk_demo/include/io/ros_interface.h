#pragma once

#include <mutex>
#include <string>

#include <opencv2/core/mat.hpp>

#include "baton_mini.h"

#ifdef ROS2
#include <builtin_interfaces/msg/time.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/imu.hpp>
#else
#include <nav_msgs/Odometry.h>
#include <ros/ros.h>
#include <sensor_msgs/Image.h>
#include <sensor_msgs/Imu.h>
#endif

namespace baton_mini_sdk_demo {

#ifdef ROS2
using ros_odom = nav_msgs::msg::Odometry;
using ros_imu = sensor_msgs::msg::Imu;
using ros_image = sensor_msgs::msg::Image;
using RosStamp = builtin_interfaces::msg::Time;
#else
using ros_odom = nav_msgs::Odometry;
using ros_imu = sensor_msgs::Imu;
using ros_image = sensor_msgs::Image;
using RosStamp = ros::Time;
#endif

class ROS_IO {
public:
  ROS_IO();
  ~ROS_IO();

  static void init(int argc, char** argv, const std::string& node_name);
  static void shutdown();
  static bool ok();
  static void spin();
  static double nowSec();

  template <typename ParameterT>
  void param(const std::string& name, ParameterT& value, const ParameterT& default_value);

  void initPublishers(std::string& server_ip, std::string& local_ip);

  void publishOdom(const odom_t& odom);
  void publishFastOdom(const odom_pack& odom);
  void publishImu(const imu_data& imu);
  void publishImageLeft(const cv::Mat& image);
  void publishImageRight(const cv::Mat& image);

  bool publishImuEnabled() const { return publish_imu_; }
  bool publishOdomEnabled() const { return publish_odom_; }
  bool publishFastOdomEnabled() const { return publish_fast_odom_; }
  bool publishImageLeftEnabled() const { return publish_image_left_; }
  bool publishImageRightEnabled() const { return publish_image_right_; }

  static void info(const char* message);

  template <typename... Args>
  static void info(const char* format, Args... args);

  static void warn(const char* message);

  template <typename... Args>
  static void warn(const char* format, Args... args);

  static void error(const char* message);

  template <typename... Args>
  static void error(const char* format, Args... args);

private:
  static RosStamp nowStamp();
  static void setStamp(RosStamp& stamp, double stamp_sec);

  void publishImage(const cv::Mat& image, const char* frame_id, bool is_left);

#ifdef ROS2
  static rclcpp::Node::SharedPtr& node();
  static rclcpp::Logger logger();

  rclcpp::Publisher<ros_imu>::SharedPtr imu_pub_;
  rclcpp::Publisher<ros_odom>::SharedPtr odom_pub_;
  rclcpp::Publisher<ros_odom>::SharedPtr fast_odom_pub_;
  rclcpp::Publisher<ros_image>::SharedPtr image_left_pub_;
  rclcpp::Publisher<ros_image>::SharedPtr image_right_pub_;
#else
  ros::NodeHandle nh_;
  ros::NodeHandle pnh_;

  ros::Publisher imu_pub_;
  ros::Publisher odom_pub_;
  ros::Publisher fast_odom_pub_;
  ros::Publisher image_left_pub_;
  ros::Publisher image_right_pub_;
#endif

  std::string imu_topic_;
  std::string odom_topic_;
  std::string fast_odom_topic_;
  std::string image_left_topic_;
  std::string image_right_topic_;

  bool publish_imu_;
  bool publish_odom_;
  bool publish_fast_odom_;
  bool publish_image_left_;
  bool publish_image_right_;

  std::mutex sim_stamp_mutex_;
  RosStamp sim_stamp_;
  bool sim_stamp_left_flag_;
  bool sim_stamp_right_flag_;
};

template <typename ParameterT>
void ROS_IO::param(const std::string& name,
                   ParameterT& value,
                   const ParameterT& default_value) {
#ifdef ROS2
  if (!node()->has_parameter(name)) {
    node()->declare_parameter<ParameterT>(name, default_value);
  }
  value = node()->get_parameter(name).template get_value<ParameterT>();
#else
  pnh_.param<ParameterT>(name, value, default_value);
#endif
}

inline void ROS_IO::info(const char* message) {
#ifdef ROS2
  RCLCPP_INFO(logger(), "%s", message ? message : "");
#else
  ROS_INFO("%s", message ? message : "");
#endif
}

template <typename... Args>
void ROS_IO::info(const char* format, Args... args) {
#ifdef ROS2
  RCLCPP_INFO(logger(), format, args...);
#else
  ROS_INFO(format, args...);
#endif
}

inline void ROS_IO::warn(const char* message) {
#ifdef ROS2
  RCLCPP_WARN(logger(), "%s", message ? message : "");
#else
  ROS_WARN("%s", message ? message : "");
#endif
}

template <typename... Args>
void ROS_IO::warn(const char* format, Args... args) {
#ifdef ROS2
  RCLCPP_WARN(logger(), format, args...);
#else
  ROS_WARN(format, args...);
#endif
}

inline void ROS_IO::error(const char* message) {
#ifdef ROS2
  RCLCPP_ERROR(logger(), "%s", message ? message : "");
#else
  ROS_ERROR("%s", message ? message : "");
#endif
}

template <typename... Args>
void ROS_IO::error(const char* format, Args... args) {
#ifdef ROS2
  RCLCPP_ERROR(logger(), format, args...);
#else
  ROS_ERROR(format, args...);
#endif
}

}  // namespace baton_mini_sdk_demo
