#ifndef SCANNER_RESAMPLER_H
#define SCANNER_RESAMPLER_H

#include "ffmpeg-wrapper.h"
#include "media.h"

extern "C" {
#include <libswscale/swscale.h>
}

// 1. automatically scale
// 2. automatically convert pixel formats
struct Resampler
{
    explicit Resampler(const av::vformat_t& fmt, const int flags = SWS_POINT)
        : fmt_(fmt), flags_(flags)
    {}

    ~Resampler();

    av::frame scale(const av::frame& src);

private:
    av::vformat_t fmt_{};
    int           flags_{ SWS_POINT };
    SwsContext   *ctx_{};
};

#endif //! SCANNER_RESAMPLER_H