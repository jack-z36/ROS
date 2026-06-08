#include "hand-panel.h"

#include "graphics/model.h"
#include "graphics/render-item-lut.h"
#include "graphics/rhi-widget.h"

#include <QApplication>
#include <QVBoxLayout>

HandDockWidget::HandDockWidget(const QString& title, const QString& rl, QWidget *parent,
                               const Qt::WindowFlags flags)
    : DockWidget(title, parent, flags)
{
    setMinimumHeight(160);

    texture_widget_ = new RhiWidget();
    texture_widget_->hfilp(rl == "L");
    layout_->addWidget(texture_widget_);

    texture_widget_->draw(std::make_shared<Model>(qApp->applicationDirPath() + "/models/RH56E2-R.gltf",
                                                  glm::scale(glm::mat4{ 1.0f }, glm::vec3{ 0.35f })));

    t12_                = std::make_shared<ImageRenderItem>();
    glm::quat rotationZ = glm::angleAxis(glm::radians(6.0f), glm::vec3{ 0.0f, 0.0f, 1.0f });
    glm::quat rotationX = glm::angleAxis(glm::radians(17.0f), glm::vec3{ 1.0f, 0.0f, 0.0f });
    glm::quat rotation  = rotationZ * rotationX;
    t12_->transform(glm::vec3{ 0.325f }, rotation, { -3.4f, 9.6f, -2.2f });
    texture_widget_->draw(t12_);

    t13_      = std::make_shared<ImageRenderItem>();
    rotationZ = glm::angleAxis(glm::radians(2.0f), glm::vec3{ 0.0f, 0.0f, 1.0f });
    rotationX = glm::angleAxis(glm::radians(-10.0f), glm::vec3{ 1.0f, 0.0f, 0.0f });
    rotation  = rotationZ * rotationX;
    t13_->transform(glm::vec3{ 0.325f }, { rotation }, { -3.9f, 4.6f, 1.9f });
    texture_widget_->draw(t13_);

    t22_      = std::make_shared<ImageRenderItem>();
    rotationZ = glm::angleAxis(glm::radians(2.0f), glm::vec3{ 0.0f, 0.0f, 1.0f });
    rotationX = glm::angleAxis(glm::radians(19.3f), glm::vec3{ 1.0f, 0.0f, 0.0f });
    rotation  = rotationZ * rotationX;
    t22_->transform(glm::vec3{ 0.325f }, rotation, { -1.5f, 10.6f, -2.85f });
    texture_widget_->draw(t22_);

    t23_      = std::make_shared<ImageRenderItem>();
    rotationZ = glm::angleAxis(glm::radians(0.0f), glm::vec3{ 0.0f, 0.0f, 1.0f });
    rotationX = glm::angleAxis(glm::radians(-7.0f), glm::vec3{ 1.0f, 0.0f, 0.0f });
    rotation  = rotationZ * rotationX;
    t23_->transform(glm::vec3{ 0.325f }, { rotation }, { -1.6f, 4.8f, 1.9f });
    texture_widget_->draw(t23_);

    t32_      = std::make_shared<ImageRenderItem>();
    rotationZ = glm::angleAxis(glm::radians(0.0f), glm::vec3{ 0.0f, 0.0f, 1.0f });
    rotationX = glm::angleAxis(glm::radians(19.0f), glm::vec3{ 1.0f, 0.0f, 0.0f });
    rotation  = rotationZ * rotationX;
    t32_->transform(glm::vec3{ 0.325f }, rotation, { 0.75f, 10.8f, -2.8f });
    texture_widget_->draw(t32_);

    t33_      = std::make_shared<ImageRenderItem>();
    rotationZ = glm::angleAxis(glm::radians(0.0f), glm::vec3{ 0.0f, 0.0f, 1.0f });
    rotationX = glm::angleAxis(glm::radians(-8.0f), glm::vec3{ 1.0f, 0.0f, 0.0f });
    rotation  = rotationZ * rotationX;
    t33_->transform(glm::vec3{ 0.325f }, { rotation }, { 0.75f, 4.8f, 1.9f });
    texture_widget_->draw(t33_);

    t42_      = std::make_shared<ImageRenderItem>();
    rotationZ = glm::angleAxis(glm::radians(-2.5f), glm::vec3{ 0.0f, 0.0f, 1.0f });
    rotationX = glm::angleAxis(glm::radians(19.0f), glm::vec3{ 1.0f, 0.0f, 0.0f });
    rotation  = rotationZ * rotationX;
    t42_->transform(glm::vec3{ 0.325f }, rotation, { 2.9f, 10.4f, -2.8f });
    texture_widget_->draw(t42_);

    t43_      = std::make_shared<ImageRenderItem>();
    rotationZ = glm::angleAxis(glm::radians(0.0f), glm::vec3{ 0.0f, 0.0f, 1.0f });
    rotationX = glm::angleAxis(glm::radians(-8.0f), glm::vec3{ 1.0f, 0.0f, 0.0f });
    rotation  = rotationZ * rotationX;
    t43_->transform(glm::vec3{ 0.325f }, { rotation }, { 3.2f, 4.8f, 1.9f });
    texture_widget_->draw(t43_);

    t52_                = std::make_shared<ImageRenderItem>();
    rotationZ           = glm::angleAxis(glm::radians(-3.6f), glm::vec3{ 0.0f, 0.0f, 1.0f });
    rotationX           = glm::angleAxis(glm::radians(18.6f), glm::vec3{ 1.0f, 0.0f, 0.0f });
    glm::quat rotationY = glm::angleAxis(glm::radians(20.0f), glm::vec3{ 0.0f, 1.0f, 0.0f });
    rotation            = rotationZ * rotationX * rotationY;
    t52_->transform(glm::vec3{ 0.325f }, rotation, { 1.9f, 3.85f, 7.20f });
    texture_widget_->draw(t52_);

    t54_      = std::make_shared<ImageRenderItem>();
    rotationZ = glm::angleAxis(glm::radians(-38.0f), glm::vec3{ 0.0f, 0.0f, 1.0f });
    rotationX = glm::angleAxis(glm::radians(60.0f), glm::vec3{ 1.0f, 0.0f, 0.0f });
    rotationY = glm::angleAxis(glm::radians(47.0f), glm::vec3{ 0.0f, 1.0f, 0.0f });
    rotation  = rotationZ * rotationX * rotationY;
    t54_->transform(glm::vec3{ 0.325f }, { rotation }, { 1.2f, 2.6f, 4.1f });
    texture_widget_->draw(t54_);

    t61_ = std::make_shared<ImageRenderItem>();
    t61_->transform(glm::vec3{ 0.7f, -0.7f, 0.7f },
                    { glm::angleAxis(glm::radians(90.0f), glm::vec3{ 0.0f, 0.0f, 1.0f }) },
                    { 0.0f, 0.0f, 0.5f });
    texture_widget_->draw(t61_);
}

void HandDockWidget::preset(const int id, const av::frame& frame) const
{
    switch (id) {
    case 0x12: t12_->attach(frame); break;
    case 0x13: t13_->attach(frame); break;
    case 0x22: t22_->attach(frame); break;
    case 0x23: t23_->attach(frame); break;
    case 0x32: t32_->attach(frame); break;
    case 0x33: t33_->attach(frame); break;
    case 0x42: t42_->attach(frame); break;
    case 0x43: t43_->attach(frame); break;
    case 0x52: t52_->attach(frame); break;
    case 0x54: t54_->attach(frame); break;
    case 0x61: t61_->attach(frame); break;
    default:   break;
    }

    texture_widget_->updateRequest();
}
