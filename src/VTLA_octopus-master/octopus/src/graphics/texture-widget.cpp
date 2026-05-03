#include "texture-widget.h"

#include "utils.h"
#include "utils/logging.h"

// clang-format off
// normalized device coordinates
static constexpr float vertices[] = {
    -1.0f, -1.0f,  /* bottom left  */  0.0f, 1.0f, /* top    left  */
    +1.0f, -1.0f,  /* bottom right */  1.0f, 1.0f, /* top    right */
    -1.0f, +1.0f,  /* top    left  */  0.0f, 0.0f, /* bottom left  */
    +1.0f, +1.0f,  /* top    right */  1.0f, 0.0f, /* bottom right */
};
// clang-format on

TextureWidget::TextureWidget(QWidget *parent)
    : QRhiWidget(parent)
{
    connect(this, &TextureWidget::updateRequest, this, [this] { update(); }, Qt::QueuedConnection);
}

AVPixelFormat TextureWidget::format(const AVPixelFormat expected, const AVPixelFormat dft)
{
    for (const auto& fmt : av::texture_formats()) {
        if (fmt == expected) {
            return expected;
        }
    }

    return dft;
}

av::vformat_t get_video_format(const av::frame& frame)
{
    return av::vformat_t{
        .width               = frame->width,
        .height              = frame->height,
        .pix_fmt             = static_cast<AVPixelFormat>(frame->format),
        .sample_aspect_ratio = frame->sample_aspect_ratio,
        .color =
            av::vformat_t::color_t{
                .space     = frame->colorspace,
                .range     = frame->color_range,
                .primaries = frame->color_primaries,
                .transfer  = frame->color_trc,
            },
    };
}

void TextureWidget::present(const av::frame& frame)
{
    if (!frame || !frame->data[0] || frame->width <= 0 || frame->height <= 0 ||
        frame->format == AV_PIX_FMT_NONE) {
        return;
    }

    std::scoped_lock lock(mtx_);
    frame_    = frame;
    image_sz_ = QSize{ frame->width, frame->height };

    if (const auto vfmt = get_video_format(frame); fmt_ != vfmt) {
        fmt_     = vfmt;
        created_ = false;
    }
    uploaded_ = false;

    emit updateRequest();
}

void TextureWidget::initialize(QRhiCommandBuffer *)
{
    if (rhi_ != rhi()) {
        pipeline_.reset();
        created_ = false;
        rhi_     = rhi();
    }

    if (!pipeline_) {}
}

void TextureWidget::create()
{
    if (created_ && pipeline_) return;

    vbuf_.reset(rhi_->newBuffer(QRhiBuffer::Immutable, QRhiBuffer::VertexBuffer, sizeof(vertices)));
    vbuf_->create();

    ubuf_.reset(rhi_->newBuffer(QRhiBuffer::Dynamic, QRhiBuffer::UniformBuffer, 64 + 64 + 16));
    ubuf_->create();

    sampler_.reset(rhi_->newSampler(QRhiSampler::Linear, QRhiSampler::Linear, QRhiSampler::None,
                                    QRhiSampler::ClampToEdge, QRhiSampler::ClampToEdge));
    sampler_->create();

    srb_.reset(rhi_->newShaderResourceBindings());
    const auto params = av::get_texture_desc(fmt_.pix_fmt);

    std::vector<QRhiShaderResourceBinding> bindings{};
    bindings.emplace_back(QRhiShaderResourceBinding::uniformBuffer(
        0, QRhiShaderResourceBinding::VertexStage | QRhiShaderResourceBinding::FragmentStage, ubuf_.get()));

    planes_.clear();
    for (size_t i = 0; i < params.size(); ++i) {
        const auto texture = rhi_->newTexture(
            params[i].format, { fmt_.width / params[i].scale_x, fmt_.height / params[i].scale_y });
        texture->create();

        bindings.emplace_back(QRhiShaderResourceBinding::sampledTexture(
            static_cast<int>(i + 1), QRhiShaderResourceBinding::FragmentStage, texture, sampler_.get()));

        planes_.emplace_back(texture);
    }
    srb_->setBindings(bindings.begin(), bindings.end());
    srb_->create();

    pipeline_.reset(rhi_->newGraphicsPipeline());
    pipeline_->setTopology(QRhiGraphicsPipeline::TriangleStrip);
    pipeline_->setShaderStages({
        { QRhiShaderStage::Vertex, utils::load_shader(":/resources/shaders/video.vert.qsb") },
        { QRhiShaderStage::Fragment, utils::load_shader(av::get_frag_shader_path(fmt_, false)) },
    });

    QRhiVertexInputLayout layout{};
    layout.setBindings({ 4 * sizeof(float) });
    layout.setAttributes({
        { 0, 0, QRhiVertexInputAttribute::Float2, 0 },
        { 0, 1, QRhiVertexInputAttribute::Float2, 2 * sizeof(float) },
    });
    pipeline_->setVertexInputLayout(layout);
    pipeline_->setShaderResourceBindings(srb_.get());
    pipeline_->setRenderPassDescriptor(renderTarget()->renderPassDescriptor());
    pipeline_->create();

    created_ = true;
}

void TextureWidget::upload(QRhiResourceUpdateBatch *rub, const QMatrix4x4& mvp)
{
    std::scoped_lock lock(mtx_);

    if (!frame_ || frame_->width <= 0 || frame_->height <= 0 || !frame_->data[0]) return;
    if (!uploaded_.exchange(true)) {
        const auto params = av::get_texture_desc(fmt_.pix_fmt);

        frame_slots_[rhi_->currentFrameSlot()] = frame_;
        for (size_t i = 0; i < params.size(); ++i) {
            QRhiTextureSubresourceUploadDescription desc(
                frame_->data[i], frame_->linesize[i] * frame_->height / params[i].scale_y);
            desc.setDataStride(frame_->linesize[i]);
            rub->uploadTexture(planes_[i].get(), QRhiTextureUploadDescription{ { 0, 0, desc } });
        }

        rub->uploadStaticBuffer(vbuf_.get(), vertices);
    }

    rub->updateDynamicBuffer(ubuf_.get(), 0, 64, mvp.constData());
    rub->updateDynamicBuffer(ubuf_.get(), 64, 64, av::get_color_matrix_coefficients(fmt_));
}

void TextureWidget::render(QRhiCommandBuffer *cb)
{
    const auto rub = rhi_->nextResourceUpdateBatch();

    const auto rtsz     = renderTarget()->pixelSize();
    render_sz_          = image_sz_.scaled(rtsz, Qt::KeepAspectRatio);
    const float scale_x = static_cast<float>(render_sz_.width()) / static_cast<float>(rtsz.width());
    const float scale_y = static_cast<float>(render_sz_.height()) / static_cast<float>(rtsz.height());

    mvp_.setToIdentity();
    mvp_.scale(scale_x, scale_y);
    create();
    upload(rub, mvp_);

    cb->beginPass(renderTarget(), Qt::black, { 1.0f, 0 }, rub);

    cb->setGraphicsPipeline(pipeline_.get());
    cb->setViewport({ 0, 0, static_cast<float>(rtsz.width()), static_cast<float>(rtsz.height()) });
    cb->setShaderResources(srb_.get());

    const QRhiCommandBuffer::VertexInput input{ vbuf_.get(), 0 };
    cb->setVertexInput(0, 1, &input);
    cb->draw(4);

    cb->endPass();
}
