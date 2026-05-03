#version 440
#extension GL_GOOGLE_include_directive: enable

#include "uniformbuffer.glsl"

layout (location = 0) in vec2 position;
layout (location = 1) in vec2 tex;

layout (location = 0) out vec2 texCoord;

void main()
{
    gl_Position = ubuf.mvp * vec4(position, 0.0f, 1.0f);
    texCoord = tex;
}
