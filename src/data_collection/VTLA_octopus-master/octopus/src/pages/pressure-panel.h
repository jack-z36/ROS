#ifndef SCANNER_PRESSURE_PANEL_H
#define SCANNER_PRESSURE_PANEL_H

#include "media/queue.h"
#include "widgets/dock-widget.h"

#include <hwk_pressure_interfaces/msg/pressure_frame.hpp>

#include <array>

class QLabel;
class PressureHeatmapWidget;
class QTimer;

class PressureDockWidget final : public DockWidget
{
    Q_OBJECT
public:
    explicit PressureDockWidget(const QString& title, QWidget *parent = nullptr,
                                Qt::WindowFlags flags = Qt::WindowFlags());

    void preset(const hwk_pressure_interfaces::msg::PressureFrame& frame);

private:
    void refresh();
    void update_frame(const hwk_pressure_interfaces::msg::PressureFrame& frame);
    void update_heatmaps();

    std::array<QPointer<PressureHeatmapWidget>, 2> heatmaps_{};
    std::array<QPointer<QLabel>, 2> stats_{};
    std::array<hwk_pressure_interfaces::msg::PressureFrame, 2> latest_;
    std::array<bool, 2> has_latest_{ false, false };

    QPointer<QTimer> timer_{};
    safe_queue<hwk_pressure_interfaces::msg::PressureFrame> frames_{ 64 };
};

#endif //! SCANNER_PRESSURE_PANEL_H
