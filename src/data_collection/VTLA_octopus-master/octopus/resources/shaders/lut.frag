#version 440

layout (location = 0) in vec3 Normal;
layout (location = 1) in vec3 FragPosition;
layout (location = 2) in vec2 texCoord;

layout (location = 0) out vec4 fragColor;

layout (binding = 1) uniform sampler2D gray;
layout (binding = 2) uniform sampler2D lut;

void main()
{
    float l = texture(gray, texCoord).r;
    vec3 c = texture(lut, vec2(0, l)).bgr;

    fragColor = vec4(c, sqrt(l));
}
