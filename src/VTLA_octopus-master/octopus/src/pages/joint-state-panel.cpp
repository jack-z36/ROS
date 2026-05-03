#include "joint-state-panel.h"

#include "utils/config.h"
#include "widgets/chart-view.h"

#include <QChart>
#include <QDateTime>
#include <QGraphicsSimpleTextItem>

JointStateDockWidget::JointStateDockWidget(const QString& title, QWidget *parent,
                                           const Qt::WindowFlags flags)
    : DockWidget(title, parent, flags)
{
    setMinimumHeight(160);

    chart_view_ = new ChartView(this);
    chart_view_->setRenderHint(QPainter::Antialiasing);
    chart_view_->setContentsMargins({});
    layout_->addWidget(chart_view_);

    {
        chart_ = new QChart();
        chart_->setMargins({});
        chart_->setAnimationOptions(QChart::NoAnimation);
        chart_->legend()->setVisible(false);
        chart_view_->setChart(chart_);

        axis_x_ = new QDateTimeAxis();
        axis_y_ = new QValueAxis();

        chart_->addAxis(axis_x_, Qt::AlignBottom);
        chart_->addAxis(axis_y_, Qt::AlignLeft);

        axis_x_->setFormat("hh:mm:ss");
        axis_x_->setTickCount(10);
        axis_x_->setGridLineVisible(false);

        axis_y_->setRange(0, 1000);
        axis_y_->setTickCount(4);
        axis_y_->setLabelFormat("%d");
    }

    chart_->setTheme(config::theme == "dark" ? QChart::ChartThemeDark : QChart::ChartThemeLight);
    chart_->setBackgroundBrush(
        QBrush(config::theme == "dark" ? QColor(24, 24, 25) : QColor(255, 255, 255)));

    timer_ = new QTimer(this);
    timer_->start(100); // ms
    connect(timer_, &QTimer::timeout, this, &JointStateDockWidget::refresh);
}

void JointStateDockWidget::add_channel(const std::string& name)
{
    series_[name] = new QSplineSeries();
    chart_->addSeries(series_[name]);

    series_[name]->setName(name.c_str());
    series_[name]->attachAxis(axis_x_);
    series_[name]->attachAxis(axis_y_);
    buffers_[name] = QList<QPointF>{};
}

void JointStateDockWidget::preset(const sensor_msgs::msg::JointState& joint_state)
{
    states_.push(joint_state);
}

void JointStateDockWidget::refresh()
{
    if (!alive()) return;

    while (true) {
        auto js = states_.pop();
        if (!js) break;

        for (const auto& [joint, pos] : std::views::zip(js.value().name, js.value().position)) {
            if (!series_.contains(joint)) {
                add_channel(joint);
            }

            const auto now = QDateTime::currentDateTime().toMSecsSinceEpoch();
            buffers_[joint].append(QPointF{ static_cast<qreal>(now), pos });
        }
    }

    for (const auto& [joint, series] : series_) {
        while (buffers_[joint].size() > capacity_) {
            buffers_[joint].removeFirst();
        }

        series->replace(buffers_[joint]);
    }

    for (const auto& v : buffers_ | std::views::values) {
        axis_x_->setRange(QDateTime::fromMSecsSinceEpoch(v.first().x()),
                          QDateTime::fromMSecsSinceEpoch(v.back().x()));
        break;
    }
}
