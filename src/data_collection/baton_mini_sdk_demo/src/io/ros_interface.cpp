#include "io/ros_interface.h"

#include <cmath>
#include <cstdint>
#include <cstring>

namespace baton_mini_sdk_demo {

namespace {

constexpr int kImuQueueDepth = 50;
constexpr int kOdomQueueDepth = 10;
constexpr int kImageQueueDepth = 5;

}  // namespace

ROS_IO::ROS_IO()
#ifdef ROS2
    : publish_imu_(true),
      publish_odom_(true),
      publish_fast_odom_(true),
      publish_image_left_(true),
      publish_image_right_(true),
      sim_stamp_(),
      sim_stamp_left_flag_(false),
      sim_stamp_right_flag_(false) {}
#else
    : nh_(),
      pnh_("~"),
      publish_imu_(true),
      publish_odom_(true),
      publish_fast_odom_(true),
      publish_image_left_(true),
      publish_image_right_(true),
      sim_stamp_(),
      sim_stamp_left_flag_(false),
      sim_stamp_right_flag_(false) {}
#endif

ROS_IO::~ROS_IO() {}

void ROS_IO::init(int argc, char** argv, const std::string& node_name) {
#ifdef ROS2
  if (!rclcpp::ok()) {
    rclcpp::init(argc, argv);
  }
  if (!node()) {
    rclcpp::NodeOptions options;
    options.automatically_declare_parameters_from_overrides(true);
    node() = std::make_shared<rclcpp::Node>(node_name, options);
  }
#else
  ros::init(argc, argv, node_name);
#endif
}

void ROS_IO::shutdown() {
#ifdef ROS2
  node().reset();
  if (rclcpp::ok()) {
    rclcpp::shutdown();
  }
#else
  ros::shutdown();
#endif
}

bool ROS_IO::ok() {
#ifdef ROS2
  return rclcpp::ok();
#else
  return ros::ok();
#endif
}

void ROS_IO::spin() {
#ifdef ROS2
  if (node()) {
    rclcpp::spin(node());
  }
#else
  ros::spin();
#endif
}

double ROS_IO::nowSec() {
#ifdef ROS2
  return node() ? node()->get_clock()->now().seconds() : 0.0;
#else
  return ros::Time::now().toSec();
#endif
}

void ROS_IO::initPublishers(std::string& server_ip, std::string& local_ip) {
  param<std::string>("server_ip", server_ip, server_ip);
  param<std::string>("local_ip", local_ip, local_ip);
  param<std::string>("imu_topic", imu_topic_, "/baton_mini/imu");
  param<std::string>("odom_topic", odom_topic_, "/baton_mini/odometry");
  param<std::string>("fast_odom_topic", fast_odom_topic_, "/baton_mini/fast_odom");
  param<std::string>("image_left_topic", image_left_topic_, "/baton_mini/image_left");
  param<std::string>("image_right_topic", image_right_topic_, "/baton_mini/image_right");
  param<bool>("publish_imu", publish_imu_, true);
  param<bool>("publish_odometry", publish_odom_, true);
  param<bool>("publish_fast_odom", publish_fast_odom_, true);
  param<bool>("publish_image_left", publish_image_left_, true);
  param<bool>("publish_image_right", publish_image_right_, true);

#ifdef ROS2
  if (publish_imu_) {
    imu_pub_ = node()->create_publisher<ros_imu>(imu_topic_, kImuQueueDepth);
  }
  if (publish_odom_) {
    odom_pub_ = node()->create_publisher<ros_odom>(odom_topic_, kOdomQueueDepth);
  }
  if (publish_fast_odom_) {
    fast_odom_pub_ = node()->create_publisher<ros_odom>(fast_odom_topic_, kOdomQueueDepth);
  }
  if (publish_image_left_) {
    image_left_pub_ = node()->create_publisher<ros_image>(image_left_topic_, kImageQueueDepth);
  }
  if (publish_image_right_) {
    image_right_pub_ = node()->create_publisher<ros_image>(image_right_topic_, kImageQueueDepth);
  }
#else
  if (publish_imu_) {
    imu_pub_ = nh_.advertise<ros_imu>(imu_topic_, kImuQueueDepth);
  }
  if (publish_odom_) {
    odom_pub_ = nh_.advertise<ros_odom>(odom_topic_, kOdomQueueDepth);
  }
  if (publish_fast_odom_) {
    fast_odom_pub_ = nh_.advertise<ros_odom>(fast_odom_topic_, kOdomQueueDepth);
  }
  if (publish_image_left_) {
    image_left_pub_ = nh_.advertise<ros_image>(image_left_topic_, kImageQueueDepth);
  }
  if (publish_image_right_) {
    image_right_pub_ = nh_.advertise<ros_image>(image_right_topic_, kImageQueueDepth);
  }
#endif
}

void ROS_IO::publishOdom(const odom_t& odom) {
  if (!publish_odom_) {
    return;
  }

  ros_odom msg;
  msg.header.stamp = nowStamp();
  msg.header.frame_id = "odom";
  msg.pose.pose.position.x = odom.pose.px;
  msg.pose.pose.position.y = odom.pose.py;
  msg.pose.pose.position.z = odom.pose.pz;
  msg.pose.pose.orientation.x = odom.pose.qx;
  msg.pose.pose.orientation.y = odom.pose.qy;
  msg.pose.pose.orientation.z = odom.pose.qz;
  msg.pose.pose.orientation.w = odom.pose.qw;
  msg.twist.twist.linear.x = odom.speed.lx;
  msg.twist.twist.linear.y = odom.speed.ly;
  msg.twist.twist.linear.z = odom.speed.lz;
  msg.twist.twist.angular.x = odom.speed.ax;
  msg.twist.twist.angular.y = odom.speed.ay;
  msg.twist.twist.angular.z = odom.speed.az;

#ifdef ROS2
  if (odom_pub_) {
    odom_pub_->publish(msg);
  }
#else
  odom_pub_.publish(msg);
#endif
}

void ROS_IO::publishFastOdom(const odom_pack& odom) {
  if (!publish_fast_odom_) {
    return;
  }

  ros_odom msg;
  setStamp(msg.header.stamp, odom.t_s);
  msg.header.frame_id = "odom";
  msg.pose.pose.position.x = odom.pose.px;
  msg.pose.pose.position.y = odom.pose.py;
  msg.pose.pose.position.z = odom.pose.pz;
  msg.pose.pose.orientation.x = odom.pose.qx;
  msg.pose.pose.orientation.y = odom.pose.qy;
  msg.pose.pose.orientation.z = odom.pose.qz;
  msg.pose.pose.orientation.w = odom.pose.qw;
  msg.twist.twist.linear.x = odom.twist.lx;
  msg.twist.twist.linear.y = odom.twist.ly;
  msg.twist.twist.linear.z = odom.twist.lz;
  msg.twist.twist.angular.x = odom.twist.ax;
  msg.twist.twist.angular.y = odom.twist.ay;
  msg.twist.twist.angular.z = odom.twist.az;

#ifdef ROS2
  if (fast_odom_pub_) {
    fast_odom_pub_->publish(msg);
  }
#else
  fast_odom_pub_.publish(msg);
#endif
}

void ROS_IO::publishImu(const imu_data& imu) {
  if (!publish_imu_) {
    return;
  }

  const RosStamp stamp = nowStamp();
  if (imu.keyframe) {
    std::lock_guard<std::mutex> lock(sim_stamp_mutex_);
    sim_stamp_ = stamp;
    sim_stamp_left_flag_ = true;
    sim_stamp_right_flag_ = true;
  }

  ros_imu msg;
  msg.header.stamp = stamp;
  msg.header.frame_id = "imu";
  msg.linear_acceleration.x = imu.acc_x;
  msg.linear_acceleration.y = imu.acc_y;
  msg.linear_acceleration.z = imu.acc_z;
  msg.angular_velocity.x = imu.gyro_x;
  msg.angular_velocity.y = imu.gyro_y;
  msg.angular_velocity.z = imu.gyro_z;

#ifdef ROS2
  if (imu_pub_) {
    imu_pub_->publish(msg);
  }
#else
  imu_pub_.publish(msg);
#endif
}

void ROS_IO::publishImageLeft(const cv::Mat& image) {
  publishImage(image, "cam_left", true);
}

void ROS_IO::publishImageRight(const cv::Mat& image) {
  publishImage(image, "cam_right", false);
}

RosStamp ROS_IO::nowStamp() {
#ifdef ROS2
  RosStamp stamp;
  if (node()) {
    setStamp(stamp, node()->get_clock()->now().seconds());
  }
  return stamp;
#else
  return ros::Time::now();
#endif
}

void ROS_IO::setStamp(RosStamp& stamp, double stamp_sec) {
#ifdef ROS2
  if (stamp_sec <= 0.0) {
    stamp.sec = 0;
    stamp.nanosec = 0;
    return;
  }

  const double floored = std::floor(stamp_sec);
  stamp.sec = static_cast<int32_t>(floored);
  int64_t nanosec = static_cast<int64_t>(std::llround((stamp_sec - floored) * 1e9));
  if (nanosec >= 1000000000LL) {
    ++stamp.sec;
    nanosec -= 1000000000LL;
  }
  if (nanosec < 0) {
    nanosec = 0;
  }
  stamp.nanosec = static_cast<uint32_t>(nanosec);
#else
  stamp = ros::Time(stamp_sec);
#endif
}

void ROS_IO::publishImage(const cv::Mat& image, const char* frame_id, bool is_left) {
  if ((is_left && !publish_image_left_) || (!is_left && !publish_image_right_)) {
    return;
  }

  if (image.empty()) {
    return;
  }

  RosStamp stamp = nowStamp();
  {
    std::lock_guard<std::mutex> lock(sim_stamp_mutex_);
    bool& use_sim_stamp = is_left ? sim_stamp_left_flag_ : sim_stamp_right_flag_;
    if (use_sim_stamp) {
      stamp = sim_stamp_;
      use_sim_stamp = false;
    }
  }

  ros_image msg;
  msg.header.stamp = stamp;
  msg.header.frame_id = frame_id ? frame_id : "";
  msg.height = static_cast<decltype(msg.height)>(image.rows);
  msg.width = static_cast<decltype(msg.width)>(image.cols);
  msg.encoding = "mono8";
  msg.is_bigendian = false;
  msg.step = static_cast<decltype(msg.step)>(image.step);

  const size_t row_bytes = static_cast<size_t>(image.cols) * image.elemSize();
  msg.data.resize(static_cast<size_t>(msg.step) * static_cast<size_t>(msg.height));
  if (image.isContinuous()) {
    const size_t size = static_cast<size_t>(image.total()) * image.elemSize();
    msg.data.assign(image.data, image.data + size);
  } else {
    for (int row = 0; row < image.rows; ++row) {
      std::memcpy(&msg.data[static_cast<size_t>(row) * msg.step], image.ptr(row), row_bytes);
    }
  }

#ifdef ROS2
  if (is_left) {
    if (image_left_pub_) {
      image_left_pub_->publish(msg);
    }
  } else if (image_right_pub_) {
    image_right_pub_->publish(msg);
  }
#else
  if (is_left) {
    image_left_pub_.publish(msg);
  } else {
    image_right_pub_.publish(msg);
  }
#endif
}

#ifdef ROS2
rclcpp::Node::SharedPtr& ROS_IO::node() {
  static rclcpp::Node::SharedPtr node_ptr;
  return node_ptr;
}

rclcpp::Logger ROS_IO::logger() {
  return node() ? node()->get_logger() : rclcpp::get_logger("baton_mini");
}
#endif

}  // namespace baton_mini_sdk_demo
