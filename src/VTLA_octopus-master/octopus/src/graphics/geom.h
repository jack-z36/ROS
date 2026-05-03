#ifndef SCANNER_GRAPHICS_GEOM_H
#define SCANNER_GRAPHICS_GEOM_H

#include <glm/mat4x4.hpp>
#include <glm/vec2.hpp>
#include <glm/vec3.hpp>
#include <vector>

enum class geom_t
{
    plane,
    cube,
    sphere,
    cylinder,
    torus,
    cone,
};

namespace geom
{
    struct vertex
    {
        glm::vec3 position{};
        glm::vec3 normal{};
        glm::vec2 coords{};
    };

    struct mesh
    {
        std::vector<vertex>   vertices{};
        std::vector<uint32_t> indices{};
        glm::mat4             transform{};
    };

    mesh make_cube();
    mesh make_sphere(uint32_t XSegN, uint32_t YSegN);
    mesh make_plane(uint32_t XSegN, uint32_t YSegN);
} // namespace geom

#endif //! SCANNER_GRAPHICS_GEOM_H