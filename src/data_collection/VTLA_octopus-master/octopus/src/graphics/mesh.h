#ifndef RHI_MESH_H
#define RHI_MESH_H

#include "geom.h"
#include "render-item.h"

#include <assimp/material.h>

struct Texture
{
    aiTextureType                type{};
    std::shared_ptr<QRhiTexture> target{};
    std::string                  path{};
};

struct Material
{
    std::string name{};

    Texture base_color{};
    Texture normal{};
    Texture metallic{};
    Texture roughness{};
    Texture ao{};

    std::array<float, 4> base_color_factor{ 0.2f, 0.2f, 0.2f, 1.0f };
    float                metallic_factor{ 0.034f };
    float                roughness_factor{ 0.650f };
};

class Mesh final : public RenderItem
{
public:
    Mesh(std::vector<geom::vertex> vertices, std::vector<uint32_t> indices, Material material,
         const glm::mat4& transform);

    Mesh(Mesh&&) = default;

    void create(QRhi *rhi, QRhiRenderTarget *rt) override;
    void upload(QRhiResourceUpdateBatch *rub, const std::array<glm::mat4, 3>& mvp) override;
    void draw(QRhiCommandBuffer *cb, const QRhiViewport& viewport) override;

    std::vector<geom::vertex> vertices{};
    std::vector<uint32_t>     indices{};
    Material                  material{};

private:
    QRhi *rhi_{};

    std::unique_ptr<QRhiGraphicsPipeline>       pipeline_{};
    std::unique_ptr<QRhiBuffer>                 vbuf_{};
    std::unique_ptr<QRhiBuffer>                 ibuf_{};
    std::unique_ptr<QRhiBuffer>                 ubuf_{};
    std::unique_ptr<QRhiBuffer>                 fbuf_{}; // pbr factors
    std::unique_ptr<QRhiSampler>                sampler_{};
    std::unique_ptr<QRhiShaderResourceBindings> srb_{};

    bool uploaded_{};
};

#endif //! RHI_MESH_H
