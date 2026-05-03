#ifndef SCANNER_UTILS_H
#define SCANNER_UTILS_H

#include <assimp/matrix4x4.h>
#include <glm/mat4x4.hpp>
#include <QFile>

namespace utils
{
    inline glm::mat4 to_mat4(aiMatrix4x4 aim)
    {
        return {
            aim.a1, aim.b1, aim.c1, aim.d1, aim.a2, aim.b2, aim.c2, aim.d2,
            aim.a3, aim.b3, aim.c3, aim.d3, aim.a4, aim.b4, aim.c4, aim.d4,
        };
    }

    inline QShader load_shader(const QString& name)
    {
        QFile f(name);
        return f.open(QIODevice::ReadOnly) ? QShader::fromSerialized(f.readAll()) : QShader();
    }
} // namespace utils

#endif //! SCANNER_UTILS_H
