#include "render-item-lut.h"

#include "glm/ext/matrix_transform.hpp"
#include "utils.h"
#include "utils/colormap.h"

#include <QFile>

// clang-format off
// normalized device coordinates
static constexpr float vertices[] = {
    -1.0f, -1.0f, 0.0f, /* bottom left  */ 0.0f, 0.0f, 1.0f, /* */ 0.0f, 1.0f, /* top    left  */
    +1.0f, -1.0f, 0.0f, /* bottom right */ 0.0f, 0.0f, 1.0f, /* */ 1.0f, 1.0f, /* top    right */
    -1.0f, +1.0f, 0.0f, /* top    left  */ 0.0f, 0.0f, 1.0f, /* */ 0.0f, 0.0f, /* bottom left  */
    +1.0f, +1.0f, 0.0f, /* top    right */ 0.0f, 0.0f, 1.0f, /* */ 1.0f, 0.0f, /* bottom right */
};
// clang-format on

void ImageRenderItem::attach(const av::frame& frame)
{
    if (frame->format == AV_PIX_FMT_GRAY8 && frame->width > 0 && frame->height > 0) {
        std::scoped_lock lock(mtx_);
        frame_ = frame;

        if (vfmt_.width != frame->width || vfmt_.height != frame->height) {
            vfmt_.width  = frame->width;
            vfmt_.height = frame->height;
            scale_.x     = static_cast<float>(vfmt_.width) / std::max(vfmt_.width, vfmt_.height);
            scale_.y     = static_cast<float>(vfmt_.height) / std::max(vfmt_.width, vfmt_.height);
            dirty_       = true;
        }

        uploaded_ = false;
    }
}

void ImageRenderItem::cmap(const cmap::colormap_t cmap) { cmap_ = cmap; }

void ImageRenderItem::create(QRhi *rhi, QRhiRenderTarget *rt)
{
    if (rhi_ != rhi) {
        pipeline_.reset();
        rhi_ = rhi;
    }

    if (dirty_.exchange(false) || !pipeline_) {
        vbuf_.reset(rhi_->newBuffer(QRhiBuffer::Immutable, QRhiBuffer::VertexBuffer, sizeof(vertices)));
        vbuf_->create();

        ubuf_.reset(rhi_->newBuffer(QRhiBuffer::Dynamic, QRhiBuffer::UniformBuffer, 64 * 3));
        ubuf_->create();

        sampler_.reset(rhi_->newSampler(QRhiSampler::Linear, QRhiSampler::Linear, QRhiSampler::None,
                                        QRhiSampler::ClampToEdge, QRhiSampler::ClampToEdge));
        sampler_->create();

        texture_.reset(rhi_->newTexture(QRhiTexture::R8, { vfmt_.width, vfmt_.height }));
        texture_->create();

        lut_.reset(rhi_->newTexture(QRhiTexture::RGBA8, { 1, 256 }));
        lut_->create();

        srb_.reset(rhi_->newShaderResourceBindings());
        srb_->setBindings({
            QRhiShaderResourceBinding::uniformBuffer(
                0, QRhiShaderResourceBinding::VertexStage | QRhiShaderResourceBinding::FragmentStage,
                ubuf_.get()),
            QRhiShaderResourceBinding::sampledTexture(1, QRhiShaderResourceBinding::FragmentStage,
                                                      texture_.get(), sampler_.get()),
            QRhiShaderResourceBinding::sampledTexture(2, QRhiShaderResourceBinding::FragmentStage,
                                                      lut_.get(), sampler_.get()),
        });
        srb_->create();

        pipeline_.reset(rhi_->newGraphicsPipeline());
        pipeline_->setTopology(QRhiGraphicsPipeline::TriangleStrip);
        pipeline_->setShaderStages({
            { QRhiShaderStage::Vertex, utils::load_shader(":/resources/shaders/vertex.vert.qsb") },
            { QRhiShaderStage::Fragment, utils::load_shader(":/resources/shaders/lut.frag.qsb") },
        });

        QRhiVertexInputLayout layout{};
        layout.setBindings({ 8 * sizeof(float) });
        layout.setAttributes({
            { 0, 0, QRhiVertexInputAttribute::Float3, 0 },
            { 0, 1, QRhiVertexInputAttribute::Float3, 3 * sizeof(float) },
            { 0, 2, QRhiVertexInputAttribute::Float2, 6 * sizeof(float) },
        });
        pipeline_->setVertexInputLayout(layout);
        pipeline_->setShaderResourceBindings(srb_.get());
        pipeline_->setRenderPassDescriptor(rt->renderPassDescriptor());
        pipeline_->setDepthTest(true);
        pipeline_->setDepthWrite(true);
        // pipeline_->setCullMode(QRhiGraphicsPipeline::Back);
        QRhiGraphicsPipeline::TargetBlend blend{
            .enable   = true,
            .srcColor = QRhiGraphicsPipeline::SrcAlpha,
        };
        pipeline_->setTargetBlends({ blend });
        pipeline_->create();
    }
}

void ImageRenderItem::upload(QRhiResourceUpdateBatch *rub, const std::array<glm::mat4, 3>& mvp)
{
    if (!uploaded_ && frame_.get() && frame_->width * frame_->height != 0) {
        rub->uploadStaticBuffer(vbuf_.get(), vertices);

        std::scoped_lock lock(mtx_);

        QRhiTextureSubresourceUploadDescription desc(frame_->data[0], frame_->linesize[0] * frame_->height);
        desc.setDataStride(frame_->linesize[0]);
        rub->uploadTexture(texture_.get(), QRhiTextureUploadDescription{ { 0, 0, desc } });

        QRhiTextureSubresourceUploadDescription lut(cmap::lut(cmap_), 1024);
        rub->uploadTexture(lut_.get(), QRhiTextureUploadDescription{ { 0, 0, lut } });

        uploaded_ = true;
    }

    auto rmvp = mvp;
    rmvp[0]   = glm::scale(mvp[0], scale_);
    rub->updateDynamicBuffer(ubuf_.get(), 0, 64 * 3, rmvp.data());
}

void ImageRenderItem::draw(QRhiCommandBuffer *cb, const QRhiViewport& viewport)
{
    cb->setGraphicsPipeline(pipeline_.get());
    cb->setViewport(viewport);
    cb->setShaderResources();

    const QRhiCommandBuffer::VertexInput input{ vbuf_.get(), 0 };
    cb->setVertexInput(0, 1, &input);
    cb->draw(4);
}
