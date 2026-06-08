#ifndef MCAP_RECORDER_H
#define MCAP_RECORDER_H

#include "media/clock.h"

#include <mcap/types.hpp>
#include <rclcpp/executors/single_threaded_executor.hpp>

namespace mcap
{
    class McapWriter;
}
class McapRecorder
{
public:
    McapRecorder();
    ~McapRecorder();

    void subscribe_topics(const std::vector<std::string>& topics);

    int record(const std::string& filename, mcap::Compression cm);

    std::chrono::nanoseconds duration() const;

    [[nodiscard]] bool running() const { return running_; }

private:
    void create_channel(const std::string& topic, const std::string& type, const rclcpp::QoS& qos);
    void create_subscription(const std::string& topic, const std::string& type, const rclcpp::QoS& qos);

    rclcpp::QoS qos_for_topic(const std::string& topic, const std::string& type) const;

    std::string get_message_definition(const std::string& type) const;

    std::shared_ptr<rclcpp::Node>                              node_{};
    std::shared_ptr<rclcpp::executors::SingleThreadedExecutor> executor_{};
    std::jthread                                               thread_{};

    std::unordered_map<std::string, std::string>                                  topics_{};
    std::unordered_map<std::string, std::shared_ptr<rclcpp::GenericSubscription>> subscriptions_{};
    std::unordered_map<std::string, mcap::ChannelId>                              channels_{};
    std::unordered_map<std::string, mcap::SchemaId>                               schemas_{};

    std::unique_ptr<mcap::McapWriter> writer_{};

    std::unordered_map<std::string, int64_t> last_write_ns_;

    std::atomic<bool>        running_{};
    std::chrono::nanoseconds start_time_{ av::clock::nopts };
};

#endif //! MCAP_RECORDER_H
