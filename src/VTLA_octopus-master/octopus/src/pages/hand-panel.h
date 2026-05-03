#ifndef SCANNER_HAND_PANEL_H
#define SCANNER_HAND_PANEL_H

#include "media/ffmpeg-wrapper.h"
#include "widgets/dock-widget.h"

class ImageRenderItem;
class RhiWidget;

class HandDockWidget final : public DockWidget
{
    Q_OBJECT
public:
    explicit HandDockWidget(const QString& title, const QString& rl, QWidget *parent = nullptr,
                            Qt::WindowFlags flags = Qt::WindowFlags());

    void preset(int id, const av::frame& frame) const;

private:
    QPointer<RhiWidget>              texture_widget_{};
    std::shared_ptr<ImageRenderItem> t12_;
    std::shared_ptr<ImageRenderItem> t13_;
    std::shared_ptr<ImageRenderItem> t22_;
    std::shared_ptr<ImageRenderItem> t23_;
    std::shared_ptr<ImageRenderItem> t32_;
    std::shared_ptr<ImageRenderItem> t33_;
    std::shared_ptr<ImageRenderItem> t42_;
    std::shared_ptr<ImageRenderItem> t43_;
    std::shared_ptr<ImageRenderItem> t52_;
    std::shared_ptr<ImageRenderItem> t54_;
    std::shared_ptr<ImageRenderItem> t61_;
};

#endif //! SCANNER_HAND_PANEL_H