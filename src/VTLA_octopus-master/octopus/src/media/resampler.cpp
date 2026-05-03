#include "resampler.h"

Resampler::~Resampler() { sws_freeContext(ctx_); }

av::frame Resampler::scale(const av::frame& src)
{
    ctx_ = sws_getCachedContext(ctx_, src->width, src->height, static_cast<AVPixelFormat>(src->format),
                                fmt_.width, fmt_.height, fmt_.pix_fmt, flags_, nullptr, nullptr, nullptr);

    av::frame dst;

    dst->width  = fmt_.width;
    dst->height = fmt_.height;
    dst->format = fmt_.pix_fmt;
    dst->pts    = src->pts;

    av_frame_get_buffer(dst.get(), 0);

    sws_scale(ctx_, src->data, src->linesize, 0, src->height, dst->data, dst->linesize);

    return dst;
}