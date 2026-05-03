#ifndef GRAPHICS_RENDER_ITEM_IMAGE_H
#define GRAPHICS_RENDER_ITEM_IMAGE_H

#include "utils/colormap.h"
#include "media/ffmpeg-wrapper.h"
#include "media/media.h"
#include "render-item.h"

class ImageRenderItem final : public RenderItem
{
public:
    ImageRenderItem() = default;

    void attach(const av::frame& frame);

    void cmap(cmap::colormap_t cmap);

protected:
    void create(QRhi *rhi, QRhiRenderTarget *rt) override;
    void upload(QRhiResourceUpdateBatch *rub, const std::array<glm::mat4, 3>& mvp) override;
    void draw(QRhiCommandBuffer *cb, const QRhiViewport& viewport) override;

private:
    QRhi *rhi_{};

    std::unique_ptr<QRhiGraphicsPipeline>       pipeline_{};
    std::unique_ptr<QRhiBuffer>                 vbuf_{};
    std::unique_ptr<QRhiBuffer>                 ubuf_{};
    std::unique_ptr<QRhiSampler>                sampler_{};
    std::unique_ptr<QRhiShaderResourceBindings> srb_{};
    std::unique_ptr<QRhiTexture>                texture_{};
    std::unique_ptr<QRhiTexture>                lut_{};

    std::mutex mtx_{};

    av::vformat_t    vfmt_{ .pix_fmt = AV_PIX_FMT_GRAY8 };
    av::frame        frame_{};
    cmap::colormap_t cmap_{ cmap::colormap_t::JET };
    glm::vec3        scale_{ 1.0f };

    std::atomic<bool> uploaded_{};
    std::atomic<bool> dirty_{ true };
};

#endif //! GRAPHICS_RENDER_ITEM_IMAGE_H