#include "geom.h"

#include <numbers>

namespace geom
{
    mesh make_cube() { return {}; }

    mesh make_sphere(const uint32_t XSegN, const uint32_t YSegN)
    {
        mesh m{};

        const float dYaw   = static_cast<float>(2.0f * std::numbers::pi / XSegN);
        const float dPitch = static_cast<float>(std::numbers::pi / YSegN);

        for (uint32_t i = 0; i <= XSegN; ++i) {
            const float yaw = i * dYaw;
            const float U   = static_cast<float>(i) / static_cast<float>(XSegN);

            for (uint32_t j = 0; j <= YSegN; ++j) {
                const float pitch = static_cast<float>(-std::numbers::pi / 2 - j * dPitch);
                const float V     = static_cast<float>(j) / static_cast<float>(YSegN);

                const float x = std::cos(pitch) * std::cos(yaw);
                const float y = std::cos(pitch) * std::sin(yaw);
                const float z = std::sin(pitch);

                m.vertices.emplace_back(glm::vec3{ x, y, z }, glm::normalize(glm::vec3{ x, y, z }),
                                        glm::vec2{ U, V });
            }
        }

        for (uint32_t i = 0; i < XSegN; ++i) {
            for (uint32_t j = 0; j < YSegN; ++j) {
                m.indices.push_back(i * (YSegN + 1) + j);
                m.indices.push_back((i + 1) * (YSegN + 1) + j);
                m.indices.push_back(i * (YSegN + 1) + j + 1);
                m.indices.push_back(i * (YSegN + 1) + j + 1);
                m.indices.push_back((i + 1) * (YSegN + 1) + j);
                m.indices.push_back((i + 1) * (YSegN + 1) + j + 1);
            }
        }

        return m;
    }

    mesh make_plane(uint32_t, uint32_t) { return {}; }

} // namespace geom
