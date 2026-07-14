#include "pressure-panel.h"

#include <QDateTime>
#include <QGridLayout>
#include <QLabel>
#include <QPainter>
#include <QPainterPath>
#include <QSizePolicy>
#include <QTimer>
#include <QVBoxLayout>
#include <QWidget>

#include <algorithm>
#include <cmath>
#include <limits>
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

    void set_frame(const hwk_pressure_interfaces::msg::PressureFrame& frame)
    {
        data_ = frame.data;
        cached_ = QImage();
        update();
    }

protected:
    void resizeEvent(QResizeEvent *e) override
    {
        QWidget::resizeEvent(e);
        mask_ = QImage();
        cached_ = QImage();
    }

    void paintEvent(QPaintEvent *) override
    {
        QPainter p(this);
        p.setRenderHint(QPainter::Antialiasing, false);

        if (data_.empty()) {
            p.fillRect(rect(), QColor(32, 32, 34));
            p.setPen(QColor(160, 160, 160));
            p.drawText(rect(), Qt::AlignCenter, QObject::tr("No data"));
            return;
        }

        if (cached_.isNull()) buildImage();
        p.drawImage(rect(), cached_);
    }

private:
    static constexpr int kRows = 8;
    static constexpr int kCols = 10;
    // Display-only absolute reference point.  It never rescales to the
    // current frame, so equal physical loads retain equal colours over time.
    static constexpr double kCellFullScaleGrams = 300.0;
    static constexpr int kMap[kRows][kCols] = {
        { -1, -1,  0,  1,  2,  3,  4,  5, -1, -1},
        { -1, -1,  6,  7,  8,  9, 10, 11, -1, -1},
        { 12, 13, 14, 15, 16, 17, 18, 19, 20, 21},
        { 22, 23, 24, 25, 26, 27, 28, 29, 30, 31},
        { 32, 33, 34, 35, 36, 37, 38, 39, 40, 41},
        { 42, 43, 44, 45, 46, 47, 48, 49, 50, 51},
        { 52, 53, 54, 55, 56, 57, 58, 59, 60, 61},
        { -1, 62, 63, 64, 65, 66, 67, 68, 69, -1},
    };

    static QPainterPath fingerPath()
    {
        // Match the physical tactile cover: a rounded cap, nearly vertical
        // sides, and a flat base.
        QPainterPath p;

        // Start at the top centre and trace the right half clockwise.
        p.moveTo(5.0, 0.0);
        p.cubicTo(7.35, 0.0, 9.25, 1.2, 9.3, 2.8);
        p.cubicTo(9.45, 4.4, 9.45, 6.3, 9.35, 8.0);
        p.lineTo(0.65, 8.0);
        p.cubicTo(0.55, 6.3, 0.55, 4.4, 0.7, 2.8);
        p.cubicTo(0.75, 1.2, 2.65, 0.0, 5.0, 0.0);
        p.closeSubpath();
        return p;
    }

    void ensureMask()
    {
        const int w = std::max(1, width());
        const int h = std::max(1, height());
        if (!mask_.isNull() && mask_.width() == w && mask_.height() == h) return;

        const double sx = w / static_cast<double>(kCols);
        const double sy = h / static_cast<double>(kRows);

        mask_ = QImage(w, h, QImage::Format_Alpha8);
        mask_.fill(0);
        QPainter mp(&mask_);
        mp.setRenderHint(QPainter::Antialiasing, true);
        mp.scale(sx, sy);
        mp.setPen(Qt::NoPen);
        mp.setBrush(Qt::white);
        mp.drawPath(fingerPath());
        mp.end();
    }

    void buildImage()
    {
        const int w = std::max(1, width());
        const int h = std::max(1, height());
        ensureMask();
        cached_ = QImage(w, h, QImage::Format_ARGB32);

        for (int py = 0; py < h; ++py) {
            const auto *mask_line = mask_.constScanLine(py);
            const double gy = (py + 0.5) * kRows / static_cast<double>(h) - 0.5;
            const int y0 = std::clamp(static_cast<int>(std::floor(gy)), 0, kRows - 1);
            const int y1 = std::clamp(y0 + 1, 0, kRows - 1);
            const double wy = gy - y0;

            auto *line = reinterpret_cast<QRgb *>(cached_.scanLine(py));
            for (int px = 0; px < w; ++px) {
                const auto ma = mask_line[px];
                if (ma == 0) {
                    line[px] = qRgba(24, 24, 26, 255);
                    continue;
                }

                const double gx = (px + 0.5) * kCols / static_cast<double>(w) - 0.5;
                const int x0 = std::clamp(static_cast<int>(std::floor(gx)), 0, kCols - 1);
                const int x1 = std::clamp(x0 + 1, 0, kCols - 1);
                const double wx = gx - x0;

                int   v00 = valid(x0, y0);  double w00 = (1 - wx) * (1 - wy);
                int   v10 = valid(x1, y0);  double w10 =      wx  * (1 - wy);
                int   v01 = valid(x0, y1);  double w01 = (1 - wx) *      wy;
                int   v11 = valid(x1, y1);  double w11 =      wx  *      wy;

                double val = 0, wsum = 0;
                if (v00 >= 0) { val += v00 * w00; wsum += w00; }
                if (v10 >= 0) { val += v10 * w10; wsum += w10; }
                if (v01 >= 0) { val += v01 * w01; wsum += w01; }
                if (v11 >= 0) { val += v11 * w11; wsum += w11; }

                if (wsum > 0) {
                    val /= wsum;
                } else {
                    // The smooth physical outline may cover a -1 map corner.
                    // Extend its nearest real sensor value instead of cutting a
                    // background-coloured notch into the mask.
                    const int nearest = nearestValid(gx, gy);
                    if (nearest < 0) {
                        line[px] = qRgba(24, 24, 26, 255);
                        continue;
                    }
                    val = nearest;
                }

                const double local_load =
                    std::clamp(val / kCellFullScaleGrams, 0.0, 1.0);

                // Keep the original high-contrast live-view palette: blue at
                // low pressure and red at high pressure.  Unlike the original
                // implementation, local_load uses a fixed absolute reference.
                const auto c = QColor::fromHsvF(
                    (1.0 - local_load) * 0.66, 0.85, 0.95);
                const auto alpha = static_cast<int>(ma);
                line[px] = qRgba(
                    (c.red()   * alpha + 24 * (255 - alpha)) / 255,
                    (c.green() * alpha + 24 * (255 - alpha)) / 255,
                    (c.blue()  * alpha + 26 * (255 - alpha)) / 255,
                    255);
            }
        }
    }

    int valid(int col, int row) const
    {
        const int idx = kMap[row][col];
        return (idx >= 0 && static_cast<size_t>(idx) < data_.size()) ? data_[idx] : -1;
    }

    int nearestValid(double gx, double gy) const
    {
        int value = -1;
        double best_distance_squared = std::numeric_limits<double>::max();
        for (int row = 0; row < kRows; ++row) {
            for (int col = 0; col < kCols; ++col) {
                const int candidate = valid(col, row);
                if (candidate < 0) continue;

                const double dx = col - gx;
                const double dy = row - gy;
                const double distance_squared = dx * dx + dy * dy;
                if (distance_squared < best_distance_squared) {
                    best_distance_squared = distance_squared;
                    value = candidate;
                }
            }
        }
        return value;
    }

    std::vector<uint16_t> data_{};
    QImage mask_{};
    QImage cached_{};
};

namespace
{
int gripper_index(const hwk_pressure_interfaces::msg::PressureFrame& frame)
{
    if (frame.gripper == "gripper_2") return 1;
    return 0;
}

double frame_force(const hwk_pressure_interfaces::msg::PressureFrame& frame)
{
    if (frame.data.empty()) return 0.0;
    // sum = total grams, convert to N: g × 1e-3 × 9.81
    constexpr double kGramsToNewton = 1e-3 * 9.81;
    const auto total = std::accumulate(frame.data.begin(), frame.data.end(), uint64_t{ 0 });
    return static_cast<double>(total) * kGramsToNewton;
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

    *stats = new QLabel(QObject::tr("F=0.000N"));
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
        update_heatmaps();
    }
}

void PressureDockWidget::update_frame(const hwk_pressure_interfaces::msg::PressureFrame& frame)
{
    const auto index = gripper_index(frame);
    latest_[index] = frame;
    has_latest_[index] = true;
}

void PressureDockWidget::update_heatmaps()
{
    for (size_t i = 0; i < latest_.size(); ++i) {
        if (!has_latest_[i]) continue;

        heatmaps_[i]->set_frame(latest_[i]);
        stats_[i]->setText(QString("F=%1N")
                               .arg(frame_force(latest_[i]), 0, 'f', 3));
    }
}
