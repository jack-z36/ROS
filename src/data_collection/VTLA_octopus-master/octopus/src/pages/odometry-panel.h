#ifndef SCANNER_ODOMETRY_PANEL_H
#define SCANNER_ODOMETRY_PANEL_H

#include "media/queue.h"
#include "widgets/dock-widget.h"

#include <nav_msgs/msg/odometry.hpp>

class ChartView;
class QChart;
class QDateTimeAxis;
class QLabel;
class QSplineSeries;
class QTimer;
class QValueAxis;

class OdometryDockWidget final : public DockWidget
{
    Q_OBJECT
public:
    explicit OdometryDockWidget(const QString& title, QWidget *parent = nullptr,
                                Qt::WindowFlags flags = Qt::WindowFlags());

    void preset(const nav_msgs::msg::Odometry& odometry);

private:
    void refresh();
    void update_values(const nav_msgs::msg::Odometry& odometry);
    void append_sample(const nav_msgs::msg::Odometry& odometry);
    void refresh_chart(qint64 now);

    QPointer<QLabel> frame_label_{};
    QPointer<QLabel> stamp_label_{};
    QPointer<QLabel> position_label_{};
    QPointer<QLabel> orientation_label_{};
    QPointer<QLabel> linear_label_{};
    QPointer<QLabel> angular_label_{};
    QPointer<QLabel> updated_label_{};

    QPointer<ChartView> chart_view_{};
    QPointer<QChart> chart_{};
    QPointer<QDateTimeAxis> axis_x_{};
    QPointer<QValueAxis> axis_y_{};
    QPointer<QSplineSeries> x_series_{};
    QPointer<QSplineSeries> y_series_{};
    QPointer<QSplineSeries> z_series_{};
    QList<QPointF> x_points_{};
    QList<QPointF> y_points_{};
    QList<QPointF> z_points_{};

    QPointer<QTimer> timer_{};
    safe_queue<nav_msgs::msg::Odometry> odometries_{ 16 };
    qint64 window_ms_{ 10000 };
};

#endif //! SCANNER_ODOMETRY_PANEL_H
