#ifndef SCANNER_MAINWINDOW_H
#define SCANNER_MAINWINDOW_H

#include "widgets/menu.h"

#include <mcap/writer.hpp>
#include <QMainWindow>
#include <QPointer>
#include <rclcpp/executors/single_threaded_executor.hpp>
#include <rclcpp/node.hpp>
#include <thread>

class OpDockWidget;
class OdometryDockWidget;
class PressureDockWidget;
class TopicsDockWidget;
class ImageDockWidget;
class QCheckBox;
class TitleBar;

class MainWindow final : public QMainWindow
{
    Q_OBJECT
public:
    explicit MainWindow(QWidget *parent = nullptr, Qt::WindowFlags flags = Qt::WindowFlags());

    ~MainWindow() override;

protected:
    void contextMenuEvent(QContextMenuEvent *event) override;

private:
    void initTitlebar();
    void initContextMenu();

    void subscribeTopics();

private:
    // titlebar
    QPointer<TitleBar>  titlebar_{};
    QPointer<QCheckBox> settings_{};
    QPointer<QCheckBox> layout_{};
    // QPointer<QCheckBox> add_panel_{};

    //
    QPointer<Menu> context_menu_{};
    QPointer<Menu> layout_menu_{};
    QPointer<Menu> add_panel_menu_{};

    QPointer<ImageDockWidget>    l_gopro_panel_{};
    QPointer<ImageDockWidget>    r_gopro_panel_{};
    QPointer<OdometryDockWidget> l_pose_panel_{};
    QPointer<OdometryDockWidget> r_pose_panel_{};
    QPointer<PressureDockWidget> l_pressure_panel_{};
    QPointer<PressureDockWidget> r_pressure_panel_{};

    // dock weights
    QPointer<TopicsDockWidget> topics_panel_{};
    QPointer<OpDockWidget>     op_panel_{};

    // display
    std::shared_ptr<rclcpp::Node>                                              sub_node_{};
    std::shared_ptr<rclcpp::executors::SingleThreadedExecutor>                 sub_executor_{};
    std::jthread                                                               sub_thread_{};
    std::unordered_map<std::string, std::shared_ptr<rclcpp::SubscriptionBase>> subscriptions_{};
};

#endif //! SCANNER_MAINWINDOW_H
