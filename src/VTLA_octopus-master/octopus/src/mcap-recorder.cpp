#define MCAP_IMPLEMENTATION

#include "mcap-recorder.h"

#include "utils/logging.h"

#include <chrono>
#include <mcap/writer.hpp>
#include <spdlog/fmt/chrono.h>
#include <spdlog/fmt/ranges.h>

using namespace std::chrono_literals;

namespace
{
// fast_odom topics are throttled from ~200Hz to 60Hz during recording.
constexpr int64_t kFastOdomMinIntervalNs = 16'666'666;

std::string reliability_to_string(const rmw_qos_reliability_policy_t reliability)
{
    switch (reliability) {
    case RMW_QOS_POLICY_RELIABILITY_RELIABLE:
        return "reliable";
    case RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT:
        return "best_effort";
    case RMW_QOS_POLICY_RELIABILITY_BEST_AVAILABLE:
        return "best_available";
    case RMW_QOS_POLICY_RELIABILITY_SYSTEM_DEFAULT:
        return "system_default";
    case RMW_QOS_POLICY_RELIABILITY_UNKNOWN:
    default:
        return "unknown";
    }
}
} // namespace

McapRecorder::McapRecorder()
{
    node_     = std::make_shared<rclcpp::Node>("recorder");
    executor_ = std::make_shared<rclcpp::executors::SingleThreadedExecutor>();
    executor_->add_node(node_);

    thread_ = std::jthread([this] { executor_->spin(); });
}

McapRecorder::~McapRecorder()
{
    executor_->cancel();
    if (thread_.joinable()) thread_.join();

    if (writer_) writer_->close();

    running_ = false;
}

void McapRecorder::subscribe_topics(const std::vector<std::string>& topics)
{
    const auto tm = node_->get_topic_names_and_types();
    for (const auto& topic : topics) {
        if (tm.contains(topic)) {
            const auto& types = tm.at(topic);
            if (types.empty()) continue;

            topics_[topic] = types[0];
        }
    }
    LOG_I("subscribe: {}", topics_);
}

void McapRecorder::create_channel(const std::string& topic, const std::string& type, const rclcpp::QoS& qos)
{
    mcap::SchemaId schema_id;
    if (!schemas_.contains(type)) {
        mcap::Schema schema(type, "ros2msg", get_message_definition(type));
        writer_->addSchema(schema);
        schemas_.emplace(type, schema.id);
        schema_id = schema.id;
    }
    else {
        schema_id = schemas_[type];
    }

    if (!channels_.contains(topic)) {
        mcap::Channel channel(topic, "cdr", schema_id);
        writer_->addChannel(channel);
        channels_.emplace(topic, channel.id);
    }

    create_subscription(topic, type, qos);
}

void McapRecorder::create_subscription(const std::string& topic, const std::string& type,
                                       const rclcpp::QoS& qos)
{
    if (subscriptions_.contains(topic)) {
        return;
    }

    LOG_I("create subscription: topic={}, type={}, reliability={}", topic, type,
          reliability_to_string(qos.get_rmw_qos_profile().reliability));

    auto subscription = node_->create_generic_subscription(
        topic, type, qos,
        [this, topic](const std::shared_ptr<const rclcpp::SerializedMessage>& message,
                      const rclcpp::MessageInfo&                              info) {
            if (topic.find("fast_odom") != std::string::npos) {
                const int64_t now_ns = info.get_rmw_message_info().source_timestamp;
                auto& last_ns = last_write_ns_[topic];
                if (now_ns - last_ns < kFastOdomMinIntervalNs) {
                    return;
                }
                last_ns = now_ns;
            }

            mcap::Message msg;
            msg.channelId   = channels_[topic];
            msg.logTime     = info.get_rmw_message_info().received_timestamp;
            msg.publishTime = info.get_rmw_message_info().source_timestamp;
            msg.dataSize    = message->get_rcl_serialized_message().buffer_length;
            msg.data        = reinterpret_cast<std::byte *>(message->get_rcl_serialized_message().buffer);
            if (!writer_->write(msg).ok()) {
                LOG_E("failed to write the message to the output file.");
            }
        });

    subscriptions_.insert(std::make_pair(topic, subscription));
}

rclcpp::QoS McapRecorder::qos_for_topic(const std::string& topic, const std::string& type) const
{
    auto qos = rclcpp::QoS(rclcpp::KeepLast(10)).reliable();

    const auto publishers = node_->get_publishers_info_by_topic(topic);
    for (const auto& publisher : publishers) {
        if (publisher.qos_profile().get_rmw_qos_profile().reliability ==
            RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT) {
            return qos.best_effort();
        }
    }

    if (publishers.empty() &&
        (type == "sensor_msgs/msg/Image" || type == "sensor_msgs/msg/CompressedImage")) {
        return qos.best_effort();
    }

    return qos;
}

int McapRecorder::record(const std::string& filename, const mcap::Compression cm)
{
    if (running_.exchange(true)) {
        LOG_W("already in running, dismissing request.");
        return -1;
    }

    if (topics_.empty()) {
        LOG_E("no available topics to record.");
        running_ = false;
        return -1;
    }

    writer_ = std::make_unique<mcap::McapWriter>();

    mcap::McapWriterOptions options{ "ros2" };
    options.compression = cm;
    if (!writer_->open(filename, options).ok()) {
        LOG_E("failed to open the output file.");
        running_ = false;
        return -1;
    }

    subscriptions_.clear();
    last_write_ns_.clear();
    start_time_ = av::clock::ns();
    for (const auto& [name, type] : topics_) {
        create_channel(name, type, qos_for_topic(name, type));
    }

    return 0;
}

std::chrono::nanoseconds McapRecorder::duration() const
{
    if (start_time_ == av::clock::nopts) return 0ns;

    return av::clock::ns() - start_time_;
}

std::string McapRecorder::get_message_definition(const std::string& type) const
{
    if (type == "sensor_msgs/msg/Image") {
        return R"(
            std_msgs/Header header

            uint32 height
            uint32 width

            string encoding
            uint8 is_bigendian
            uint32 step
            uint8[] data

            ================================================================================
            MSG: std_msgs/Header
            builtin_interfaces/Time stamp
            string frame_id

            ================================================================================
            MSG: builtin_interfaces/Time
            int32 sec
            uint32 nanosec
        )";
    }

    if (type == "sensor_msgs/msg/CompressedImage") {
        return R"(
            std_msgs/Header header

            string format
            uint8[] data

            ================================================================================
            MSG: std_msgs/Header
            builtin_interfaces/Time stamp
            string frame_id

            ================================================================================
            MSG: builtin_interfaces/Time
            int32 sec
            uint32 nanosec
        )";
    }

    if (type == "sensor_msgs/msg/JointState") {
        return R"(
            std_msgs/Header header

            string[] name
            float64[] position
            float64[] velocity
            float64[] effort

            ================================================================================
            MSG: std_msgs/Header
            builtin_interfaces/Time stamp
            string frame_id

            ================================================================================
            MSG: builtin_interfaces/Time
            int32 sec
            uint32 nanosec
        )";
    }

    if (type == "nav_msgs/msg/Odometry") {
        return R"(
            std_msgs/Header header
            string child_frame_id
            geometry_msgs/PoseWithCovariance pose
            geometry_msgs/TwistWithCovariance twist

            ================================================================================
            MSG: std_msgs/Header
            builtin_interfaces/Time stamp
            string frame_id

            ================================================================================
            MSG: builtin_interfaces/Time
            int32 sec
            uint32 nanosec

            ================================================================================
            MSG: geometry_msgs/PoseWithCovariance
            geometry_msgs/Pose pose
            float64[36] covariance

            ================================================================================
            MSG: geometry_msgs/Pose
            geometry_msgs/Point position
            geometry_msgs/Quaternion orientation

            ================================================================================
            MSG: geometry_msgs/Point
            float64 x
            float64 y
            float64 z

            ================================================================================
            MSG: geometry_msgs/Quaternion
            float64 x
            float64 y
            float64 z
            float64 w

            ================================================================================
            MSG: geometry_msgs/TwistWithCovariance
            geometry_msgs/Twist twist
            float64[36] covariance

            ================================================================================
            MSG: geometry_msgs/Twist
            geometry_msgs/Vector3 linear
            geometry_msgs/Vector3 angular

            ================================================================================
            MSG: geometry_msgs/Vector3
            float64 x
            float64 y
            float64 z
        )";
    }

    if (type == "hwk_pressure_interfaces/msg/PressureFrame") {
        return R"(
            std_msgs/Header header
            string hand
            string gripper
            uint8 device_addr
            uint8 package_id
            uint8 total_packets
            uint8 packet_index
            uint8 rows
            uint8 cols
            uint16[] data
            uint8[] raw_payload

            ================================================================================
            MSG: std_msgs/Header
            builtin_interfaces/Time stamp
            string frame_id

            ================================================================================
            MSG: builtin_interfaces/Time
            int32 sec
            uint32 nanosec
        )";
    }

    LOG_E("unsupported type {}", type);
    return {};
}
