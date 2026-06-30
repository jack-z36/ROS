#ifndef SCANNER_COLORMAP_H
#define SCANNER_COLORMAP_H

#include "utils/enum.h"

#include <cstdint>
#include <map>
#include <string>
#include <tuple>

namespace cmap
{
    enum class colormap_t : uint8_t
    {
        AUTUMN = 0x00,
        BONE,
        JET,
        WINTER,
        RAINBOW,
        OCEAN,
        SUMMER,
        SPRING,
        COOL,
        HSV,
        PINK,
        HOT,
        PARULA,
        MAGMA,
        INFERNO,
        PLASMA,
        VIRIDIS,
        CIVIDIS,
        TWILIGHT,
        TWILIGHT_SHIFTED,
        TURBO,
        DEEPGREEN,

        ENABLE_BITMASK_OPERATORS()
    };

    std::map<int, std::string> list();

    // <B, G, R>
    std::tuple<uint8_t, uint8_t, uint8_t> lookup(colormap_t, uint8_t);

    const uint8_t *lut(colormap_t = colormap_t::JET);

    const char *to_string(colormap_t);
} // namespace cmap

#endif //! SCANNER_COLORMAP_H