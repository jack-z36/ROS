#include "image-widget.h"

#include "graphics/texture-widget.h"

#include <QGridLayout>
#include <QLabel>
#include <QMetaObject>
#include <QVBoxLayout>

#include <algorithm>

using namespace std::chrono_literals;

ImageDockWidget::ImageDockWidget(const QString& title, QWidget *parent, const Qt::WindowFlags flags)
    : DockWidget(title, parent, flags)
{
    setMinimumHeight(160);

    const auto container = new QWidget(this);
    const auto grid = new QGridLayout();
    grid->setContentsMargins({});
    grid->setSpacing(0);
    container->setLayout(grid);
    layout_->addWidget(container);

    texture_widget_ = new TextureWidget();
    grid->addWidget(texture_widget_, 0, 0);

    fps_label_ = new QLabel(tr("FPS --.-  |  -- x --"), container);
    fps_label_->setAlignment(Qt::AlignLeft | Qt::AlignVCenter);
    fps_label_->setMargin(6);
    fps_label_->setAttribute(Qt::WA_TransparentForMouseEvents);
    fps_label_->setStyleSheet(
        "QLabel { background-color: rgba(0, 0, 0, 150); color: white; border-radius: 4px; }");
    grid->addWidget(fps_label_, 0, 0, Qt::AlignLeft | Qt::AlignTop);
}

void ImageDockWidget::preset(const av::frame& frame)
{
    texture_widget_->present(frame);
    update_fps_label(frame);
}

void ImageDockWidget::update_fps_label(const av::frame& frame)
{
    if (!frame || frame->width <= 0 || frame->height <= 0) return;

    const auto now = std::chrono::steady_clock::now();
    frame_times_.push_back(now);
    while (!frame_times_.empty() && now - frame_times_.front() > 2s) {
        frame_times_.pop_front();
    }

    if (last_fps_label_update_ != std::chrono::steady_clock::time_point{} &&
        now - last_fps_label_update_ < 250ms) {
        return;
    }
    last_fps_label_update_ = now;

    double fps = 0.0;
    if (frame_times_.size() > 1) {
        const auto elapsed =
            std::chrono::duration<double>(frame_times_.back() - frame_times_.front()).count();
        if (elapsed > 0.0) {
            fps = static_cast<double>(frame_times_.size() - 1) / elapsed;
        }
    }

    const auto text =
        QString("FPS %1  |  %2 x %3")
            .arg(fps, 0, 'f', 1)
            .arg(frame->width)
            .arg(frame->height);

    const QPointer<QLabel> label = fps_label_;
    QMetaObject::invokeMethod(
        this,
        [label, text] {
            if (label) {
                label->setText(text);
                label->adjustSize();
            }
        },
        Qt::QueuedConnection);
}
