#ifndef RHI_RENDER_ITEM_H
#define RHI_RENDER_ITEM_H

#define GLM_ENABLE_EXPERIMENTAL

#include <glm/ext/matrix_transform.hpp>
#include <glm/glm.hpp>
#include <glm/gtx/quaternion.hpp>
#include <rhi/qrhi.h>

struct RenderItem
{
    virtual ~RenderItem() = default;

    virtual void create(QRhi *rhi, QRhiRenderTarget *rt)                                   = 0;
    virtual void upload(QRhiResourceUpdateBatch *rub, const std::array<glm::mat4, 3>& mvp) = 0;
    virtual void draw(QRhiCommandBuffer *cb, const QRhiViewport& viewport)                 = 0;

    virtual void transform(const glm::mat4& matrix) { transform_ = matrix; }

    virtual void transform(const glm::vec3& scale, const glm::quat& rotation, const glm::vec3& translate)
    {
        transform_ = glm::translate(glm::scale(transform_, scale) * glm::toMat4(rotation), translate);
    }

    virtual void transform(const glm::vec3& scale, const float angle, const glm::vec3& axis, const glm::vec3& translate)
    {
        transform_ = glm::translate(glm::rotate(glm::scale(transform_, scale), angle, axis), translate);
    }

    virtual void scale(const glm::vec3& scale) { transform_ = glm::scale(transform_, scale); }

    virtual void rotate(const glm::quat& rotation) { transform_ *= glm::toMat4(rotation); }

    virtual void rotate(const float angle, const glm::vec3& axis)
    {
        transform_ = glm::rotate(transform_, angle, axis);
    }

    virtual void translate(const glm::vec3& translation)
    {
        transform_ = glm::translate(transform_, translation);
    }

    [[nodiscard]] virtual glm::mat4 matrix() const { return transform_; }

private:
    glm::mat4 transform_{ 1.0f };
};

#endif //! RHI_RENDER_ITEM_H
