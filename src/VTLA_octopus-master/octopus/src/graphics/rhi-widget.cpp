#include "rhi-widget.h"

#include "glm/ext/matrix_transform.hpp"
#include "model.h"

#include <QFile>
#include <QMimeData>
#include <QMouseEvent>

RhiWidget::RhiWidget(QWidget *parent, const Qt::WindowFlags f)
    : QRhiWidget(parent, f)
{
    setAcceptDrops(true);
    setSampleCount(4);

    connect(this, &RhiWidget::updateRequest, this, [this] { update(); }, Qt::QueuedConnection);
}

void RhiWidget::initialize(QRhiCommandBuffer *)
{
    if (rhi_ != rhi()) {
        rhi_ = rhi();
    }
}

void RhiWidget::draw(const std::shared_ptr<RenderItem>& item) { items_.push_back(item); }

void RhiWidget::draw(const std::vector<std::shared_ptr<RenderItem>>& items)
{
    items_.insert(items_.end(), items.begin(), items.end());
}

void RhiWidget::clear() { items_.clear(); }

void RhiWidget::render(QRhiCommandBuffer *cb)
{
    const auto rub  = rhi_->nextResourceUpdateBatch();
    const auto rtsz = renderTarget()->pixelSize();

    const auto m = glm::scale(glm::toMat4(glm::normalize(rotation_)), scale_);
    const auto p =
        glm::perspective(45.0f, rtsz.width() / static_cast<float>(rtsz.height()), 0.01f, 3000.0f);

    for (const auto& item : items_) {
        item->create(rhi_, renderTarget());
        item->upload(rub, { m * item->matrix(), camera_.getViewMatrix(), p });
    }

    cb->beginPass(renderTarget(), Qt::black, { 1.0f, 0 }, rub);

    for (const auto& item : items_) {
        item->draw(cb, { 0, 0, static_cast<float>(rtsz.width()), static_cast<float>(rtsz.height()) });
    }

    cb->endPass();
}

void RhiWidget::mousePressEvent(QMouseEvent *event)
{
    last_pos_ = { event->position().x(), event->position().y() };
    QWidget::mousePressEvent(event);
}

void RhiWidget::mouseMoveEvent(QMouseEvent *event)
{
    if (event->buttons() & Qt::MiddleButton) {
        const auto diff = glm::vec2{ event->position().x(), event->position().y() } - last_pos_;
        last_pos_       = { event->position().x(), event->position().y() };

        const auto axis = glm::normalize(glm::vec3(diff.y, diff.x, 0.0));

        rotation_ *= glm::angleAxis(glm::length(diff) / 64, axis);
        update();
    }

    QWidget::mouseMoveEvent(event);
}

void RhiWidget::wheelEvent(QWheelEvent *event)
{
    scale_ *= event->angleDelta().y() < 0 ? 0.95f : 1.05f;

    update();

    QWidget::wheelEvent(event);
}

void RhiWidget::dragEnterEvent(QDragEnterEvent *event)
{
    const auto mimedata = event->mimeData();
    if (mimedata->hasUrls()) {
        event->acceptProposedAction();
    }
    else {
        event->ignore();
    }
}

void RhiWidget::dropEvent(QDropEvent *event)
{
    items_.clear();

    for (const auto mimedata = event->mimeData(); auto& url : mimedata->urls()) {
        items_.emplace_back(std::make_shared<Model>(url.toLocalFile()));
    }

    update();
}
