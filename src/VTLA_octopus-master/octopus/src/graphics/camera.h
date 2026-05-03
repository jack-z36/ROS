#ifndef SCANNER_GRAPHICS_CAMERA_H
#define SCANNER_GRAPHICS_CAMERA_H

#include <glm/fwd.hpp>
#include <glm/vec3.hpp>

class Camera
{
public:
    explicit Camera(const glm::vec3& eye = glm::vec3{ 0.0f, 0.0f, 0.0f });
    Camera(float x, float y, float z);

    [[nodiscard]] glm::mat4 getViewMatrix() const;

    [[nodiscard]] glm::vec3 position() const { return eye_; }

private:
    glm::vec3 eye_{};
};

#endif //! SCANNER_GRAPHICS_CAMERA_H