#ifndef GRAPHICS_RENDER_ITEM_BALLS_H
#define GRAPHICS_RENDER_ITEM_BALLS_H

#include "geom.h"
#include "media/ffmpeg-wrapper.h"
#include "render-item.h"

class BallsRenderItem final : public RenderItem
{
public:
    BallsRenderItem();

    void attach(const av::frame& frame);

protected:
    void create(QRhi *rhi, QRhiRenderTarget *rt) override;
    void upload(QRhiResourceUpdateBatch *rub, const std::array<glm::mat4, 3>& mvp) override;
    void draw(QRhiCommandBuffer *cb, const QRhiViewport& viewport) override;

private:
    QRhi *rhi_{};

    std::unique_ptr<QRhiGraphicsPipeline>       pipeline_{};
    std::unique_ptr<QRhiBuffer>                 vbo_{};
    std::unique_ptr<QRhiBuffer>                 instancing_vbo_{};
    std::unique_ptr<QRhiBuffer>                 ebo_{};
    std::unique_ptr<QRhiBuffer>                 ubo_{};
    std::unique_ptr<QRhiShaderResourceBindings> srb_{};

    geom::mesh             mesh_{};
    std::vector<glm::vec2> instance_offsets_{};

    std::atomic<bool> uploaded_{};
};

#endif //! GRAPHICS_RENDER_ITEM_BALLS_H