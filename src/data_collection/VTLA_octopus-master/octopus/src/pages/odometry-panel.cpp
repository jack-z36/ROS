#include "odometry-panel.h"

#include "utils/config.h"
#include "widgets/chart-view.h"

#include <QChart>
#include <QDateTime>
#include <QDateTimeAxis>
#include <QGridLayout>
#include <QLabel>
#include <QSplineSeries>
#include <QTimer>
#include <QValueAxis>
#include <QVBoxLayout>

#include <algorithm>

namespace
{
QString vec3_text(const double x, const double y, const double z)
{
    return QString("x %1  y %2  z %3")
        .arg(x, 0, 'f', 4)
        .arg(y, 0, 'f', 4)
        .arg(z, 0, 'f', 4);
}

QString quat_text(const double x, const double y, const double z, const double w)
{
    return QString("x %1  y %2  z %3  w %4")
        .arg(x, 0, 'f', 4)
        .arg(y, 0, 'f', 4)
        .arg(z, 0, 'f', 4)
        .arg(w, 0, 'f', 4);
}

QLabel *add_value_row(QGridLayout *grid, const int row, const QString& name)
{
    const auto name_label = new QLabel(name);
    const auto value = new QLabel("-");
    value->setTextInteractionFlags(Qt::TextSelectableByMouse);
    grid->addWidget(name_label, row, 0, Qt::AlignTop);
    grid->addWidget(value, row, 1);
    return value;
}
} // namespace

OdometryDockWidget::OdometryDockWidget(const QString& title, QWidget *parent,
                                       const Qt::WindowFlags flags)
    : DockWidget(title, parent, flags)
{
    setMinimumHeight(220);

    const auto grid = new QGridLayout();
    grid->setContentsMargins({ 16, 12, 16, 8 });
    grid->setHorizontalSpacing(12);
    grid->setVerticalSpacing(6);
    layout_->addLayout(grid);

    frame_label_ = add_value_row(grid, 0, tr("Frame"));
    stamp_label_ = add_value_row(grid, 1, tr("Stamp"));
    position_label_ = add_value_row(grid, 2, tr("Position"));
    orientation_label_ = add_value_row(grid, 3, tr("Orientation"));
    linear_label_ = add_value_row(grid, 4, tr("Linear"));
    angular_label_ = add_value_row(grid, 5, tr("Angular"));
    updated_label_ = add_value_row(grid, 6, tr("Updated"));
    grid->setColumnStretch(1, 1);

    chart_view_ = new ChartView(this);
    chart_view_->setRenderHint(QPainter::Antialiasing);
    chart_view_->setContentsMargins({});
    layout_->addWidget(chart_view_, 1);

    chart_ = new QChart();
    chart_->setMargins({});
    chart_->setAnimationOptions(QChart::NoAnimation);
    chart_->legend()->setVisible(true);
    chart_view_->setChart(chart_);

    axis_x_ = new QDateTimeAxis();
    axis_y_ = new QValueAxis();
    axis_x_->setFormat("hh:mm:ss");
    axis_x_->setTickCount(5);
    axis_x_->setGridLineVisible(false);
    axis_y_->setTickCount(5);
    axis_y_->setLabelFormat("%.3f");

    chart_->addAxis(axis_x_, Qt::AlignBottom);
    chart_->addAxis(axis_y_, Qt::AlignLeft);

    x_series_ = new QSplineSeries();
    y_series_ = new QSplineSeries();
    z_series_ = new QSplineSeries();
    x_series_->setName("x");
    y_series_->setName("y");
    z_series_->setName("z");

    for (const auto series : { x_series_, y_series_, z_series_ }) {
        chart_->addSeries(series);
        series->attachAxis(axis_x_);
        series->attachAxis(axis_y_);
    }

    chart_->setTheme(config::theme == "dark" ? QChart::ChartThemeDark : QChart::ChartThemeLight);
    chart_->setBackgroundBrush(
        QBrush(config::theme == "dark" ? QColor(24, 24, 25) : QColor(255, 255, 255)));

    timer_ = new QTimer(this);
    timer_->start(100);
    connect(timer_, &QTimer::timeout, this, &OdometryDockWidget::refresh);
}

void OdometryDockWidget::preset(const nav_msgs::msg::Odometry& odometry)
{
    odometries_.push(odometry, true);
}

void OdometryDockWidget::refresh()
{
    if (!alive()) return;

    bool updated = false;
    while (true) {
        const auto odometry = odometries_.pop();
        if (!odometry) break;

        update_values(odometry.value());
        append_sample(odometry.value());
        updated = true;
    }

    if (updated) {
        refresh_chart(QDateTime::currentDateTime().toMSecsSinceEpoch());
    }
}

void OdometryDockWidget::update_values(const nav_msgs::msg::Odometry& odometry)
{
    const auto& pose = odometry.pose.pose;
    const auto& twist = odometry.twist.twist;

    frame_label_->setText(QString::fromStdString(odometry.header.frame_id));
    stamp_label_->setText(QString("%1.%2")
                              .arg(odometry.header.stamp.sec)
                              .arg(odometry.header.stamp.nanosec, 9, 10, QLatin1Char('0')));
    position_label_->setText(vec3_text(pose.position.x, pose.position.y, pose.position.z));
    orientation_label_->setText(
        quat_text(pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w));
    linear_label_->setText(vec3_text(twist.linear.x, twist.linear.y, twist.linear.z));
    angular_label_->setText(vec3_text(twist.angular.x, twist.angular.y, twist.angular.z));
    updated_label_->setText(QDateTime::currentDateTime().toString("hh:mm:ss.zzz"));
}

void OdometryDockWidget::append_sample(const nav_msgs::msg::Odometry& odometry)
{
    const auto now = QDateTime::currentDateTime().toMSecsSinceEpoch();
    const auto& p = odometry.pose.pose.position;

    x_points_.append({ static_cast<qreal>(now), p.x });
    y_points_.append({ static_cast<qreal>(now), p.y });
    z_points_.append({ static_cast<qreal>(now), p.z });
}

void OdometryDockWidget::refresh_chart(const qint64 now)
{
    const auto cutoff = now - window_ms_;
    for (auto points : { &x_points_, &y_points_, &z_points_ }) {
        while (!points->empty() && points->front().x() < cutoff) {
            points->removeFirst();
        }
    }

    x_series_->replace(x_points_);
    y_series_->replace(y_points_);
    z_series_->replace(z_points_);

    axis_x_->setRange(QDateTime::fromMSecsSinceEpoch(cutoff), QDateTime::fromMSecsSinceEpoch(now));

    qreal min_y = 0;
    qreal max_y = 0;
    bool has_value = false;
    for (const auto points : { &x_points_, &y_points_, &z_points_ }) {
        for (const auto& point : *points) {
            if (!has_value) {
                min_y = point.y();
                max_y = point.y();
                has_value = true;
            }
            else {
                min_y = std::min(min_y, point.y());
                max_y = std::max(max_y, point.y());
            }
        }
    }

    if (!has_value) {
        axis_y_->setRange(-1.0, 1.0);
        return;
    }

    const auto padding = std::max<qreal>((max_y - min_y) * 0.15, 0.05);
    axis_y_->setRange(min_y - padding, max_y + padding);
}
