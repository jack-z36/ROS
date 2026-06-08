#version 440

layout (location = 0) in vec3 Normal;
layout (location = 1) in vec3 FragPosition;
layout (location = 2) in vec2 texCoord;

layout (location = 0) out vec4 fragColor;

layout (binding = 1) uniform sampler2D plane0;

void main()
{
    fragColor = texture(plane0, texCoord).bgra;
}
