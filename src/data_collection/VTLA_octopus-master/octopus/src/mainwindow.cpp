#include "mainwindow.h"

#include "frameless/frameless-maker.h"
#include "frameless/titlebar.h"
#include "media/resampler.h"
#include "pages/image-widget.h"
#include "pages/odometry-panel.h"
#include "pages/op-panel.h"
#include "pages/pressure-panel.h"
#include "pages/settings-dialog.h"
#include "pages/topics-widget.h"
#include "scanner.h"
#include "utils/config.h"
#include "utils/logging.h"

#include <algorithm>
#include <cstring>
#include <memory>
#include <QCheckBox>
#include <QContextMenuEvent>
#include <QIcon>
#include <QLayout>
#include <hwk_pressure_interfaces/msg/pressure_frame.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>

static AVPixelFormat to_ffmpeg_pixfmt(const std::string& encoding)
{
    if (encoding == "mono8") {
        return AV_PIX_FMT_GRAY8;
    }
    if (encoding == "mono16" || encoding == "16UC1") {
        return AV_PIX_FMT_GRAY16;
    }
    if (encoding == "rgb8") {
        return AV_PIX_FMT_RGB24;
    }
    if (encoding == "bgr8") {
        return AV_PIX_FMT_BGR24;
    }
    if (encoding == "rgba8") {
        return AV_PIX_FMT_RGBA;
    }
    if (encoding == "bgra8") {
        return AV_PIX_FMT_BGRA;
    }

    LOG_E("unsupported ros2 image encoding: {}", encoding);
    return AV_PIX_FMT_RGB24;
}

static av::frame to_ffmpeg_frame(const sensor_msgs::msg::Image& img)
{
    av::frame frame{};
    frame->width  = img.width;
    frame->height = img.height;
    frame->format = to_ffmpeg_pixfmt(img.encoding);
    av_frame_get_buffer(frame.get(), 0);

    for (uint32_t i = 0; i < img.height; ++i) {
        const auto src_offset = static_cast<size_t>(i) * img.step;
        if (src_offset >= img.data.size()) break;

        const auto remaining = img.data.size() - src_offset;
        const auto copy_size =
            std::min({ static_cast<size_t>(frame->linesize[0]), static_cast<size_t>(img.step),
                       remaining });
        std::memset(frame->data[0] + i * frame->linesize[0], 0,
                    static_cast<size_t>(frame->linesize[0]));
        std::memcpy(frame->data[0] + i * frame->linesize[0], img.data.data() + src_offset,
                    copy_size);
    }
    return frame;
}

MainWindow::MainWindow(QWidget *parent, const Qt::WindowFlags flags)
    : QMainWindow(parent, flags)
{
    setWindowFlags(windowFlags() & ~Qt::WindowFullscreenButtonHint);
    setAttribute(Qt::WA_DeleteOnClose);

    titlebar_ = new TitleBar(this);
    new FramelessMaker(titlebar_, this);

    setContentsMargins({});

    setWindowTitle(tr(""));
    titlebar_->setIcon(QIcon{ ":/icons/embosenx-light" });

    // dock widgets
    topics_panel_ = new TopicsDockWidget(tr("Topics"));
    op_panel_     = new OpDockWidget(tr("Operation"));
    topics_panel_->setVisible(false);

    addDockWidget(Qt::LeftDockWidgetArea, topics_panel_);
    addDockWidget(Qt::RightDockWidgetArea, op_panel_);

    setDockNestingEnabled(true);

    l_gopro_panel_    = new ImageDockWidget(tr("Left GoPro"));
    r_gopro_panel_    = new ImageDockWidget(tr("Right GoPro"));
    l_pose_panel_     = new OdometryDockWidget(tr("Left Pose"));
    r_pose_panel_     = new OdometryDockWidget(tr("Right Pose"));
    l_pressure_panel_ = new PressureDockWidget(tr("Left Tactile"));
    r_pressure_panel_ = new PressureDockWidget(tr("Right Tactile"));

    addDockWidget(Qt::LeftDockWidgetArea, l_gopro_panel_);
    splitDockWidget(l_gopro_panel_, r_gopro_panel_, Qt::Horizontal);
    splitDockWidget(l_gopro_panel_, l_pose_panel_, Qt::Vertical);
    splitDockWidget(l_pose_panel_, l_pressure_panel_, Qt::Vertical);
    splitDockWidget(r_gopro_panel_, r_pose_panel_, Qt::Vertical);
    splitDockWidget(r_pose_panel_, r_pressure_panel_, Qt::Vertical);

    // titlebar
    initTitlebar();

    // context menu
    initContextMenu();

    resize(1280, 960);

    //
    sub_node_     = std::make_shared<rclcpp::Node>("octopus");
    sub_executor_ = std::make_shared<rclcpp::executors::SingleThreadedExecutor>();
    sub_executor_->add_node(sub_node_);
    sub_thread_ = std::jthread([this] { sub_executor_->spin(); });

    subscribeTopics();
}

MainWindow::~MainWindow()
{
    if (sub_executor_) sub_executor_->cancel();
    if (sub_thread_.joinable()) sub_thread_.join();
}

void MainWindow::contextMenuEvent(QContextMenuEvent *event) { context_menu_->exec(event->globalPos()); }

void MainWindow::initTitlebar()
{
    layout_ = new QCheckBox();
    layout_->setObjectName("layout-btn");
    layout_->setToolTip(tr("Layout"));
    layout_->setCheckable(false);
    layout_->setContextMenuPolicy(Qt::PreventContextMenu);

    // menu
    {
        layout_menu_ = new Menu(this);

        {
            const auto visible = layout_menu_->addAction(tr("Topics Panel"));
            visible->setCheckable(true);
            visible->setChecked(config::layout::visibility::topics_panel);
            topics_panel_->setVisible(config::layout::visibility::topics_panel);
            connect(visible, &QAction::triggered, topics_panel_, &DockWidget::setAlive);
            connect(topics_panel_, &DockWidget::aliveChanged, visible, &QAction::setChecked);
            connect(topics_panel_, &DockWidget::aliveChanged,
                    [](auto&& v) { config::layout::visibility::topics_panel = v; });
        }
    }

    // settings button
    settings_ = new QCheckBox();
    settings_->setObjectName("settings-btn");
    settings_->setToolTip(tr("Settings"));
    settings_->setCheckable(false);
    settings_->setContextMenuPolicy(Qt::PreventContextMenu);

    // title bar
    titlebar_->addWidget(layout_, 0, Qt::AlignRight | Qt::AlignVCenter);
    titlebar_->addWidget(settings_, 0, Qt::AlignRight | Qt::AlignVCenter);
    setMenuWidget(titlebar_);

    connect(settings_, &QCheckBox::clicked, [] {
        SettingsDialog dialog{};
        dialog.exec();
    });

    connect(layout_, &QCheckBox::clicked,
            [this] { layout_menu_->exec(mapToGlobal(layout_->geometry().bottomLeft()) + QPoint{ 0, 5 }); });
    connect(topics_panel_, &TopicsDockWidget::refresh,
            [this] { topics_panel_->update(sub_node_->get_topic_names_and_types()); });
}

void MainWindow::initContextMenu() { context_menu_ = new Menu(this); }

void MainWindow::subscribeTopics()
{
    struct ImageSubscriptionState
    {
        std::shared_ptr<Resampler> resampler{};
        int width{};
        int height{};
    };

    auto subscribe_image = [this](const std::string& topic, QPointer<ImageDockWidget> panel) {
        const auto state = std::make_shared<ImageSubscriptionState>();

        subscriptions_[topic] = sub_node_->create_subscription<sensor_msgs::msg::Image>(
            topic, rclcpp::SensorDataQoS(),
            [panel, state](const sensor_msgs::msg::Image& img) {
                if (!panel) return;

                if (!state->resampler || state->width != static_cast<int>(img.width) ||
                    state->height != static_cast<int>(img.height)) {
                    state->width = static_cast<int>(img.width);
                    state->height = static_cast<int>(img.height);
                    state->resampler = std::make_shared<Resampler>(av::vformat_t{
                        .width   = state->width,
                        .height  = state->height,
                        .pix_fmt = AV_PIX_FMT_RGBA,
                    });
                }

                panel->preset(state->resampler->scale(to_ffmpeg_frame(img)));
            });
    };

    auto subscribe_odometry = [this](const std::string& topic,
                                     QPointer<OdometryDockWidget> panel) {
        subscriptions_[topic] = sub_node_->create_subscription<nav_msgs::msg::Odometry>(
            topic, rclcpp::QoS(rclcpp::KeepLast(10)).reliable(),
            [panel](const nav_msgs::msg::Odometry& msg) {
                if (panel) panel->preset(msg);
            });
    };

    auto subscribe_pressure = [this](const std::string& topic,
                                     QPointer<PressureDockWidget> panel) {
        subscriptions_[topic] =
            sub_node_->create_subscription<hwk_pressure_interfaces::msg::PressureFrame>(
                topic, rclcpp::QoS(rclcpp::KeepLast(10)).reliable(),
                [panel](const hwk_pressure_interfaces::msg::PressureFrame& msg) {
                    if (panel) panel->preset(msg);
                });
    };

    subscribe_image("/gopro_left/image_raw", l_gopro_panel_);
    subscribe_image("/gopro_right/image_raw", r_gopro_panel_);

    subscribe_odometry("/baton_mini_left/fast_odom", l_pose_panel_);
    subscribe_odometry("/baton_mini_right/fast_odom", r_pose_panel_);

    subscribe_pressure("/pressure/left_hand/gripper_1", l_pressure_panel_);
    subscribe_pressure("/pressure/left_hand/gripper_2", l_pressure_panel_);
    subscribe_pressure("/pressure/right_hand/gripper_1", r_pressure_panel_);
    subscribe_pressure("/pressure/right_hand/gripper_2", r_pressure_panel_);
}
