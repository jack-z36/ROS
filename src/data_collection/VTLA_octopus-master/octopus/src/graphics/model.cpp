#include "model.h"

#include "utils.h"
#include "utils/logging.h"

#include <assimp/Importer.hpp>
#include <assimp/postprocess.h>
#include <assimp/scene.h>
#include <chrono>
#include <QDir>
#include <QFileInfo>

Model::Model(const QString& path, const glm::mat4& mvp)
{
    load(path);
    RenderItem::transform(mvp);
}

bool Model::load(const QString& resource)
{
    dir_ = QFileInfo{ resource }.dir().absolutePath().toStdString();

    Assimp::Importer importer{};
    const auto       scene =
        importer.ReadFile(resource.toStdString(), aiProcess_Triangulate | aiProcess_GenSmoothNormals |
                                                      aiProcess_FlipUVs | aiProcess_CalcTangentSpace);
    if (!scene || scene->mFlags & AI_SCENE_FLAGS_INCOMPLETE || !scene->mRootNode) {
        LOG_E("{}", importer.GetErrorString());
        return false;
    }

    meshes_.clear();
    textures_.clear();

    load_node(scene, scene->mRootNode, { 1.0f });

    created_  = false;
    uploaded_ = false;

    return true;
}

void Model::load_node(const aiScene *scene, const aiNode *node, const glm::mat4& accumulated_transform)
{
    const auto transform = accumulated_transform * utils::to_mat4(node->mTransformation);

    for (uint32_t i = 0; i < node->mNumMeshes; ++i) {
        load_mesh(scene, scene->mMeshes[node->mMeshes[i]], transform);
    }

    for (uint32_t i = 0; i < node->mNumChildren; ++i) {
        load_node(scene, node->mChildren[i], transform);
    }
}

void Model::load_mesh(const aiScene *scene, const aiMesh *mesh, glm::mat4 accumulated_transform)
{
    std::vector<geom::vertex> vertices{};
    for (unsigned mi = 0; mi < mesh->mNumVertices; mi++) {
        geom::vertex vertex{
            .position = { mesh->mVertices[mi].x, mesh->mVertices[mi].y, mesh->mVertices[mi].z },
        };

        if (mesh->HasNormals()) {
            vertex.normal = { mesh->mNormals[mi].x, mesh->mNormals[mi].y, mesh->mNormals[mi].z };
        }

        if (mesh->mTextureCoords[0]) {
            vertex.coords = { mesh->mTextureCoords[0][mi].x, mesh->mTextureCoords[0][mi].y };
        }

        vertices.push_back(vertex);
    }

    std::vector<uint32_t> indices{};
    for (unsigned ii = 0; ii < mesh->mNumFaces; ii++) {
        const auto face = mesh->mFaces[ii];
        for (unsigned ij = 0; ij < face.mNumIndices; ij++) {
            indices.emplace_back(face.mIndices[ij]);
        }
    }

    // load materials
    const auto aimat = scene->mMaterials[mesh->mMaterialIndex];

    Material material{};
    if (aiString name{}; AI_SUCCESS == aimat->Get(AI_MATKEY_NAME, name)) {
        material.name = name.C_Str();
    }

    // static
    if (aiColor4D base_color; AI_SUCCESS == aimat->Get(AI_MATKEY_BASE_COLOR, base_color)) {
        material.base_color_factor = { base_color.r, base_color.g, base_color.b, base_color.a };
    }

    if (ai_real metallic; AI_SUCCESS == aimat->Get(AI_MATKEY_METALLIC_FACTOR, metallic)) {
        material.metallic_factor = metallic;
    }

    if (float roughness; AI_SUCCESS == aimat->Get(AI_MATKEY_ROUGHNESS_FACTOR, roughness)) {
        material.roughness_factor = roughness;
    }

    // texture
    if (aiString path{}; AI_SUCCESS == aimat->GetTexture(aiTextureType_BASE_COLOR, 0, &path)) {
        material.base_color = {
            .type = aiTextureType_BASE_COLOR,
            .path = dir_ + "/" + std::string(path.data, path.length),
        };

        textures_[dir_ + "/" + std::string(path.data, path.length)].reset();
    }

    if (aiString path{}; AI_SUCCESS == aimat->GetTexture(aiTextureType_NORMALS, 0, &path)) {
        material.normal = {
            .type = aiTextureType_NORMALS,
            .path = dir_ + "/" + std::string(path.data, path.length),
        };

        textures_[dir_ + "/" + std::string(path.data, path.length)].reset();
    }

    if (aiString path{}; AI_SUCCESS == aimat->GetTexture(aiTextureType_METALNESS, 0, &path)) {
        material.metallic = {
            .type = aiTextureType_METALNESS,
            .path = dir_ + "/" + std::string(path.data, path.length),
        };

        textures_[dir_ + "/" + std::string(path.data, path.length)].reset();
    }

    if (aiString path{}; AI_SUCCESS == aimat->GetTexture(aiTextureType_DIFFUSE_ROUGHNESS, 0, &path)) {
        material.roughness = {
            .type = aiTextureType_DIFFUSE_ROUGHNESS,
            .path = dir_ + "/" + std::string(path.data, path.length),
        };

        textures_[dir_ + "/" + std::string(path.data, path.length)].reset();
    }

    if (aiString path{}; AI_SUCCESS == aimat->GetTexture(aiTextureType_AMBIENT_OCCLUSION, 0, &path)) {
        material.ao = {
            .type = aiTextureType_AMBIENT_OCCLUSION,
            .path = dir_ + "/" + std::string(path.data, path.length),
        };

        textures_[dir_ + "/" + std::string(path.data, path.length)].reset();
    }

    meshes_.emplace_back(std::make_unique<Mesh>(vertices, indices, material, accumulated_transform));
}

void Model::create(QRhi *rhi, QRhiRenderTarget *rt)
{
    if (!created_) {
        for (auto& [key, value] : textures_) {
            QImage image{};
            if (!image.load(QString::fromStdString(key))) continue;

            value.reset(rhi->newTexture(QRhiTexture::RGBA8, image.size()));
            value->create();
        }

        for (const auto& mesh : meshes_) {
            if (!mesh->material.base_color.path.empty()) {
                mesh->material.base_color.target = textures_[mesh->material.base_color.path];
            }

            if (!mesh->material.normal.path.empty()) {
                mesh->material.normal.target = textures_[mesh->material.normal.path];
            }

            if (!mesh->material.metallic.path.empty()) {
                mesh->material.metallic.target = textures_[mesh->material.metallic.path];
            }

            if (!mesh->material.roughness.path.empty()) {
                mesh->material.roughness.target = textures_[mesh->material.roughness.path];
            }

            if (!mesh->material.ao.path.empty()) {
                mesh->material.ao.target = textures_[mesh->material.ao.path];
            }
        }
        created_ = true;
    }

    for (auto& mesh : meshes_) {
        mesh->create(rhi, rt);
    }
}

void Model::upload(QRhiResourceUpdateBatch *rub, const std::array<glm::mat4, 3>& mvp)
{
    if (!uploaded_) {
        for (auto& [path, tex] : textures_) {
            if (QImage image{}; image.load(QString::fromStdString(path))) {
                rub->uploadTexture(tex.get(), image);
            }
        }
        uploaded_ = true;
    }

    for (auto& mesh : meshes_) {
        mesh->upload(rub, mvp);
    }
}

void Model::draw(QRhiCommandBuffer *cb, const QRhiViewport& viewport)
{
    for (const auto& mesh : meshes_) {
        mesh->draw(cb, viewport);
    }
}
