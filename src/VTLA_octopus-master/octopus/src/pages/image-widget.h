#ifndef SCANNER_VIDEO_WINDOW_H
#define SCANNER_VIDEO_WINDOW_H

#include "media/ffmpeg-wrapper.h"
#include "widgets/dock-widget.h"

#include <chrono>
#include <deque>

class QLabel;
class TextureWidget;

class ImageDockWidget final : public DockWidget
{
    Q_OBJECT
public:
    explicit ImageDockWidget(const QString& title, QWidget *parent = nullptr,
                             Qt::WindowFlags flags = Qt::WindowFlags());

    void preset(const av::frame& frame);

private:
    void update_fps_label(const av::frame& frame);

    QPointer<TextureWidget> texture_widget_{};
    QPointer<QLabel>        fps_label_{};

    std::deque<std::chrono::steady_clock::time_point> frame_times_{};
    std::chrono::steady_clock::time_point             last_fps_label_update_{};
};

#endif //! SCANNER_VIDEO_WINDOW_H
