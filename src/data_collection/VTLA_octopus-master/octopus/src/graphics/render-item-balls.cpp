#include "render-item-balls.h"

#include "glm/ext/matrix_transform.hpp"
#include "utils.h"

#include <QFile>

BallsRenderItem::BallsRenderItem()
{
    mesh_ = geom::make_sphere(30, 30);

    for (int i = -8; i < 8; i += 2) {
        for (int j = -12; j < 12; j += 2) {
            instance_offsets_.emplace_back(i * 4.0f + 4.0f, j * 4.0f + 4.0f);
        }
    }
}

void BallsRenderItem::attach(const av::frame&) {}

void BallsRenderItem::create(QRhi *rhi, QRhiRenderTarget *rt)
{
    if (rhi_ != rhi) {
        pipeline_.reset();
        rhi_ = rhi;
    }

    if (!pipeline_) {
        vbo_.reset(rhi_->newBuffer(QRhiBuffer::Immutable, QRhiBuffer::VertexBuffer,
                                   mesh_.vertices.size() * sizeof(geom::vertex)));
        vbo_->create();

        instancing_vbo_.reset(rhi_->newBuffer(QRhiBuffer::Immutable, QRhiBuffer::VertexBuffer,
                                              instance_offsets_.size() * sizeof(glm::vec2)));
        instancing_vbo_->create();

        ebo_.reset(rhi_->newBuffer(QRhiBuffer::Immutable, QRhiBuffer::IndexBuffer,
                                   static_cast<quint32>(mesh_.indices.size() * sizeof(uint32_t))));
        ebo_->create();

        ubo_.reset(rhi_->newBuffer(QRhiBuffer::Dynamic, QRhiBuffer::UniformBuffer, 64 * 3));
        ubo_->create();

        srb_.reset(rhi_->newShaderResourceBindings());
        srb_->setBindings({ QRhiShaderResourceBinding::uniformBuffer(
            0, QRhiShaderResourceBinding::VertexStage | QRhiShaderResourceBinding::FragmentStage,
            ubo_.get()) });
        srb_->create();

        pipeline_.reset(rhi_->newGraphicsPipeline());
        pipeline_->setTopology(QRhiGraphicsPipeline::Triangles);
        pipeline_->setShaderStages({
            { QRhiShaderStage::Vertex, utils::load_shader(":/resources/shaders/instancing.vert.qsb") },
            { QRhiShaderStage::Fragment, utils::load_shader(":/resources/shaders/fragment.frag.qsb") },
        });

        QRhiVertexInputLayout layout{};
        layout.setBindings({
            { 8 * sizeof(float) },
            { 2 * sizeof(float), QRhiVertexInputBinding::PerInstance },
        });
        layout.setAttributes({
            { 0, 0, QRhiVertexInputAttribute::Float3, 0 },
            { 0, 1, QRhiVertexInputAttribute::Float3, 3 * sizeof(float) },
            { 0, 2, QRhiVertexInputAttribute::Float2, 6 * sizeof(float) },
            { 1, 3, QRhiVertexInputAttribute::Float2, 0 },
        });
        pipeline_->setVertexInputLayout(layout);
        pipeline_->setShaderResourceBindings(srb_.get());
        pipeline_->setRenderPassDescriptor(rt->renderPassDescriptor());
        pipeline_->setDepthTest(true);
        pipeline_->setDepthWrite(true);
        pipeline_->setCullMode(QRhiGraphicsPipeline::Back);
        pipeline_->create();
    }
}

void BallsRenderItem::upload(QRhiResourceUpdateBatch *rub, const std::array<glm::mat4, 3>& mvp)
{
    if (!uploaded_) {
        rub->uploadStaticBuffer(vbo_.get(), mesh_.vertices.data());
        rub->uploadStaticBuffer(instancing_vbo_.get(), instance_offsets_.data());
        rub->uploadStaticBuffer(ebo_.get(), mesh_.indices.data());

        uploaded_ = true;
    }

    auto m = glm::scale(mvp[0], glm::vec3{ 0.046f });
    m      = glm::translate(m, { 0.0f, 0.0f, 0.45f * 30 });

    rub->updateDynamicBuffer(ubo_.get(), 0, 64, &m);
    rub->updateDynamicBuffer(ubo_.get(), 64, 64, &mvp[1]);
    rub->updateDynamicBuffer(ubo_.get(), 128, 64, &mvp[2]);
}

void BallsRenderItem::draw(QRhiCommandBuffer *cb, const QRhiViewport& viewport)
{
    cb->setGraphicsPipeline(pipeline_.get());
    cb->setViewport(viewport);
    cb->setShaderResources();

    const QRhiCommandBuffer::VertexInput input[] = {
        { vbo_.get(), 0 },
        { instancing_vbo_.get(), 0 },
    };
    cb->setVertexInput(0, 2, input, ebo_.get(), 0, QRhiCommandBuffer::IndexUInt32);
    cb->drawIndexed(mesh_.indices.size(), instance_offsets_.size());
}
