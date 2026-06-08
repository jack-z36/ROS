#include "pressure-panel.h"

#include <QDateTime>
#include <QGridLayout>
#include <QLabel>
#include <QPainter>
#include <QSizePolicy>
#include <QTimer>
#include <QVBoxLayout>
#include <QWidget>

#include <algorithm>
#include <numeric>
#include <vector>

class PressureHeatmapWidget final : public QWidget
{
public:
    explicit PressureHeatmapWidget(QWidget *parent = nullptr) : QWidget(parent)
    {
        setMinimumHeight(150);
        setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    }

    void set_frame(const hwk_pressure_interfaces::msg::PressureFrame& frame, const uint16_t scale_max)
    {
        rows_ = frame.rows;
        cols_ = frame.cols;
        data_ = frame.data;
        scale_max_ = std::max<uint16_t>(scale_max, 1);
        update();
    }

protected:
    void paintEvent(QPaintEvent *) override
    {
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing, false);
        painter.fillRect(rect(), QColor(32, 32, 34));

        if (rows_ == 0 || cols_ == 0 || data_.empty()) {
            painter.setPen(QColor(160, 160, 160));
            painter.drawText(rect(), Qt::AlignCenter, QObject::tr("No data"));
            return;
        }

        const auto cell_w = width() / static_cast<qreal>(cols_);
        const auto cell_h = height() / static_cast<qreal>(rows_);
        for (uint8_t row = 0; row < rows_; ++row) {
            for (uint8_t col = 0; col < cols_; ++col) {
                const auto idx = static_cast<size_t>(row) * cols_ + col;
                if (idx >= data_.size()) continue;

                const auto normalized =
                    std::clamp(data_[idx] / static_cast<qreal>(scale_max_), 0.0, 1.0);
                const auto color = QColor::fromHsvF((1.0 - normalized) * 0.66, 0.85, 0.95);
                painter.fillRect(QRectF(col * cell_w, row * cell_h, cell_w + 0.5, cell_h + 0.5),
                                 color);
            }
        }

        painter.setPen(QColor(30, 30, 30, 90));
        for (uint8_t row = 1; row < rows_; ++row) {
            const auto y = row * cell_h;
            painter.drawLine(QPointF(0, y), QPointF(width(), y));
        }
        for (uint8_t col = 1; col < cols_; ++col) {
            const auto x = col * cell_w;
            painter.drawLine(QPointF(x, 0), QPointF(x, height()));
        }
    }

private:
    uint8_t rows_{ 0 };
    uint8_t cols_{ 0 };
    uint16_t scale_max_{ 1 };
    std::vector<uint16_t> data_{};
};

namespace
{
int gripper_index(const hwk_pressure_interfaces::msg::PressureFrame& frame)
{
    if (frame.gripper == "gripper_2") return 1;
    return 0;
}

uint16_t frame_max(const hwk_pressure_interfaces::msg::PressureFrame& frame)
{
    if (frame.data.empty()) return 0;
    return *std::max_element(frame.data.begin(), frame.data.end());
}

double frame_avg(const hwk_pressure_interfaces::msg::PressureFrame& frame)
{
    if (frame.data.empty()) return 0.0;
    const auto total = std::accumulate(frame.data.begin(), frame.data.end(), uint64_t{ 0 });
    return static_cast<double>(total) / static_cast<double>(frame.data.size());
}

QWidget *make_gripper_widget(const QString& title, PressureHeatmapWidget **heatmap, QLabel **stats)
{
    const auto widget = new QWidget();
    const auto layout = new QVBoxLayout();
    layout->setContentsMargins({ 12, 10, 12, 10 });
    layout->setSpacing(8);
    widget->setLayout(layout);

    const auto label = new QLabel(title);
    label->setAlignment(Qt::AlignCenter);
    layout->addWidget(label);

    *heatmap = new PressureHeatmapWidget();
    layout->addWidget(*heatmap, 1);

    *stats = new QLabel(QObject::tr("max -  avg -  updated -"));
    (*stats)->setAlignment(Qt::AlignCenter);
    layout->addWidget(*stats);

    return widget;
}
} // namespace

PressureDockWidget::PressureDockWidget(const QString& title, QWidget *parent,
                                       const Qt::WindowFlags flags)
    : DockWidget(title, parent, flags)
{
    setMinimumHeight(220);

    const auto grid = new QGridLayout();
    grid->setContentsMargins({});
    grid->setSpacing(0);
    layout_->addLayout(grid, 1);

    PressureHeatmapWidget *gripper_1_heatmap{};
    PressureHeatmapWidget *gripper_2_heatmap{};
    QLabel *gripper_1_stats{};
    QLabel *gripper_2_stats{};

    grid->addWidget(make_gripper_widget(tr("Gripper 1"), &gripper_1_heatmap, &gripper_1_stats), 0, 0);
    grid->addWidget(make_gripper_widget(tr("Gripper 2"), &gripper_2_heatmap, &gripper_2_stats), 0, 1);
    grid->setColumnStretch(0, 1);
    grid->setColumnStretch(1, 1);

    heatmaps_[0] = gripper_1_heatmap;
    heatmaps_[1] = gripper_2_heatmap;
    stats_[0] = gripper_1_stats;
    stats_[1] = gripper_2_stats;

    timer_ = new QTimer(this);
    timer_->start(100);
    connect(timer_, &QTimer::timeout, this, &PressureDockWidget::refresh);
}

void PressureDockWidget::preset(const hwk_pressure_interfaces::msg::PressureFrame& frame)
{
    frames_.push(frame, true);
}

void PressureDockWidget::refresh()
{
    if (!alive()) return;

    bool updated = false;
    while (true) {
        const auto frame = frames_.pop();
        if (!frame) break;

        update_frame(frame.value());
        updated = true;
    }

    if (updated) {
        update_scale();
    }
}

void PressureDockWidget::update_frame(const hwk_pressure_interfaces::msg::PressureFrame& frame)
{
    const auto index = gripper_index(frame);
    latest_[index] = frame;
    has_latest_[index] = true;
}

void PressureDockWidget::update_scale()
{
    uint16_t scale_max = 1;
    for (size_t i = 0; i < latest_.size(); ++i) {
        if (has_latest_[i]) {
            scale_max = std::max(scale_max, frame_max(latest_[i]));
        }
    }

    for (size_t i = 0; i < latest_.size(); ++i) {
        if (!has_latest_[i]) continue;

        heatmaps_[i]->set_frame(latest_[i], scale_max);
        stats_[i]->setText(QString("max %1  avg %2  %3x%4  updated %5")
                               .arg(frame_max(latest_[i]))
                               .arg(frame_avg(latest_[i]), 0, 'f', 1)
                               .arg(latest_[i].rows)
                               .arg(latest_[i].cols)
                               .arg(QDateTime::currentDateTime().toString("hh:mm:ss.zzz")));
    }
}
