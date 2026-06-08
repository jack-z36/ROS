#ifndef SCANNER_JOINT_STATE_PANEL_H
#define SCANNER_JOINT_STATE_PANEL_H

#include "media/queue.h"
#include "widgets/dock-widget.h"

#include <sensor_msgs/msg/joint_state.hpp>

class QSplineSeries;
class QDateTimeAxis;
class QValueAxis;
class QChart;
class QLineSeries;
class ChartView;

class JointStateDockWidget final : public DockWidget
{
    Q_OBJECT
public:
    explicit JointStateDockWidget(const QString& title, QWidget *parent = nullptr,
                                  Qt::WindowFlags flags = Qt::WindowFlags());

    void preset(const sensor_msgs::msg::JointState& joint_state);

private:
    void add_channel(const std::string& name);
    void refresh();

    QPointer<ChartView>                                    chart_view_{};
    QPointer<QChart>                                       chart_{};
    QPointer<QDateTimeAxis>                                axis_x_{};
    QPointer<QValueAxis>                                   axis_y_{};
    std::unordered_map<std::string, QPointer<QSplineSeries>> series_{};
    std::unordered_map<std::string, QList<QPointF>>        buffers_{};
    QPointer<QTimer>                                       timer_{};
    safe_queue<sensor_msgs::msg::JointState>               states_{ 8 };
    ssize_t                                                capacity_{ 64 };
};

#endif //! SCANNER_JOINT_STATE_PANEL_H