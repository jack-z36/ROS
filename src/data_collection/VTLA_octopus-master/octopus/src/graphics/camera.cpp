#include "camera.h"

#include "glm/ext/matrix_transform.hpp"

#include <glm/mat4x4.hpp>

Camera::Camera(const glm::vec3& eye) : eye_(eye) {}

Camera::Camera(const float x, const float y, const float z) : eye_{ glm::vec3(x, y, z) } {}

glm::mat4 Camera::getViewMatrix() const
{
    return glm::lookAt(eye_, glm::vec3{ 0.0f, 0.0f, 0.0f }, glm::vec3{ 0.0f, 1.0f, 0.0f });
}
