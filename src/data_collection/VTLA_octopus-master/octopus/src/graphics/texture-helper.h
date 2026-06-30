#ifndef SCANNER_TEXTURE_HELPER_H
#define SCANNER_TEXTURE_HELPER_H

#include "media/media.h"

#include <rhi/qrhi.h>

extern "C" {
#include <libavutil/pixfmt.h>
}

namespace av
{
    struct TextureDescription
    {
        int32_t             scale_x{};
        int32_t             scale_y{};
        QRhiTexture::Format format{};
        uint32_t            bytes{};
    };

    std::vector<AVPixelFormat> texture_formats();

    std::vector<TextureDescription> get_texture_desc(AVPixelFormat fmt);
    const float                    *get_color_matrix_coefficients(const av::vformat_t& fmt);

    QString get_shader_name(const av::vformat_t& fmt, bool hdr);
    QString get_frag_shader_path(const av::vformat_t& fmt, bool hdr);
} // namespace av

#endif //! SCANNER_TEXTURE_HELPER_H
