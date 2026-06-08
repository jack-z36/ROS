#include "mesh.h"

#include "utils.h"

#include <QFile>
#include <utility>

Mesh::Mesh(std::vector<geom::vertex> vertices, std::vector<uint32_t> indices, Material material,
           const glm::mat4& transform)
    : vertices(std::move(vertices)), indices(std::move(indices)), material(std::move(material))

{
    RenderItem::transform(transform);
}

void Mesh::create(QRhi *rhi, QRhiRenderTarget *rt)
{
    if (rhi_ != rhi) {
        pipeline_.reset();
        rhi_ = rhi;
    }

    if (!pipeline_) {
        vbuf_.reset(rhi->newBuffer(QRhiBuffer::Immutable, QRhiBuffer::VertexBuffer,
                                   static_cast<quint32>(vertices.size() * sizeof(geom::vertex))));
        vbuf_->create();

        ibuf_.reset(rhi->newBuffer(QRhiBuffer::Immutable, QRhiBuffer::IndexBuffer,
                                   static_cast<quint32>(indices.size() * sizeof(uint32_t))));
        ibuf_->create();

        ubuf_.reset(rhi->newBuffer(QRhiBuffer::Dynamic, QRhiBuffer::UniformBuffer, 64 * 3));
        ubuf_->create();

        fbuf_.reset(rhi->newBuffer(QRhiBuffer::Dynamic, QRhiBuffer::UniformBuffer, 24));
        fbuf_->create();

        sampler_.reset(rhi->newSampler(QRhiSampler::Linear, QRhiSampler::Linear, QRhiSampler::None,
                                       QRhiSampler::Repeat, QRhiSampler::Repeat));
        sampler_->create();

        std::vector<QRhiShaderResourceBinding> bindings{};
        bindings.emplace_back(QRhiShaderResourceBinding::uniformBuffer(
            0, QRhiShaderResourceBinding::VertexStage | QRhiShaderResourceBinding::FragmentStage,
            ubuf_.get()));
        if (!material.base_color.path.empty()) {
            bindings.emplace_back(QRhiShaderResourceBinding::sampledTexture(
                1, QRhiShaderResourceBinding::FragmentStage, material.base_color.target.get(),
                sampler_.get()));
        }
        if (!material.normal.path.empty()) {
            bindings.emplace_back(QRhiShaderResourceBinding::sampledTexture(
                2, QRhiShaderResourceBinding::FragmentStage, material.normal.target.get(), sampler_.get()));
        }
        if (!material.metallic.path.empty()) {
            bindings.emplace_back(
                QRhiShaderResourceBinding::sampledTexture(3, QRhiShaderResourceBinding::FragmentStage,
                                                          material.metallic.target.get(), sampler_.get()));
        }
        if (!material.roughness.path.empty()) {
            bindings.emplace_back(
                QRhiShaderResourceBinding::sampledTexture(4, QRhiShaderResourceBinding::FragmentStage,
                                                          material.roughness.target.get(), sampler_.get()));
        }
        if (!material.ao.path.empty()) {
            bindings.emplace_back(QRhiShaderResourceBinding::sampledTexture(
                5, QRhiShaderResourceBinding::FragmentStage, material.ao.target.get(), sampler_.get()));
        }
        bindings.emplace_back(QRhiShaderResourceBinding::uniformBuffer(
            6, QRhiShaderResourceBinding::VertexStage | QRhiShaderResourceBinding::FragmentStage,
            fbuf_.get()));

        srb_.reset(rhi->newShaderResourceBindings());
        srb_->setBindings(bindings.begin(), bindings.end());
        srb_->create();

        pipeline_.reset(rhi->newGraphicsPipeline());
        pipeline_->setTopology(QRhiGraphicsPipeline::Triangles);
        pipeline_->setShaderStages({
            { QRhiShaderStage::Vertex, utils::load_shader(":/resources/shaders/vertex.vert.qsb") },
            { QRhiShaderStage::Fragment, utils::load_shader(":/resources/shaders/fragment.frag.qsb") },
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
        // pipeline_->setPolygonMode(QRhiGraphicsPipeline::Line);
        pipeline_->create();
    }
}

void Mesh::upload(QRhiResourceUpdateBatch *rub, const std::array<glm::mat4, 3>& mvp)
{
    if (!uploaded_) {
        rub->uploadStaticBuffer(vbuf_.get(), vertices.data());
        rub->uploadStaticBuffer(ibuf_.get(), indices.data());

        rub->updateDynamicBuffer(fbuf_.get(), 0, 16, &material.base_color_factor);
        rub->updateDynamicBuffer(fbuf_.get(), 16, 4, &material.metallic_factor);
        rub->updateDynamicBuffer(fbuf_.get(), 20, 4, &material.roughness_factor);

        uploaded_ = true;
    }

    auto rmvp = mvp;
    rmvp[0]   = rmvp[0] * matrix();
    rub->updateDynamicBuffer(ubuf_.get(), 0, 64 * 3, rmvp.data());
}

void Mesh::draw(QRhiCommandBuffer *cb, const QRhiViewport& viewport)
{
    cb->setGraphicsPipeline(pipeline_.get());
    cb->setViewport(viewport);
    cb->setShaderResources();

    const QRhiCommandBuffer::VertexInput input{ vbuf_.get(), 0 };
    cb->setVertexInput(0, 1, &input, ibuf_.get(), 0, QRhiCommandBuffer::IndexUInt32);
    cb->drawIndexed(static_cast<quint32>(indices.size()));
}