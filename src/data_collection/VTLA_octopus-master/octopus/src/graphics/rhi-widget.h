#ifndef RHI_WIDGET_H
#define RHI_WIDGET_H

#include "camera.h"
#include "render-item.h"

#define GLM_ENABLE_EXPERIMENTAL
#include <glm/gtx/quaternion.hpp>
#include <QRhiWidget>
#include <rhi/qrhi.h>

class RhiWidget final : public QRhiWidget
{
    Q_OBJECT

public:
    explicit RhiWidget(QWidget *parent = nullptr, Qt::WindowFlags f = {});

    void draw(const std::shared_ptr<RenderItem>& item);

    void draw(const std::vector<std::shared_ptr<RenderItem>>& items);

    void clear();

    void hfilp(const bool flip) { scale_[0] *= flip ? -1.0f : 1.0f; }

signals:
    void updateRequest();

protected:
    void initialize(QRhiCommandBuffer *) override;
    void render(QRhiCommandBuffer *cb) override;

    void mousePressEvent(QMouseEvent *event) override;
    void mouseMoveEvent(QMouseEvent *event) override;
    void wheelEvent(QWheelEvent *event) override;

    void dragEnterEvent(QDragEnterEvent *event) override;
    void dropEvent(QDropEvent *event) override;

private:
    QRhi *rhi_{};

    Camera camera_{ 0.0f, 0.0f, 8.0f };

    // mouse
    glm::vec2 last_pos_{};
    glm::quat rotation_{ 1.0f, 0.0f, 0.0f, 0.0f };
    glm::vec3 scale_{ 1.0f };

    std::vector<std::shared_ptr<RenderItem>> items_{};
};

#endif //! RHI_WIDGET_H