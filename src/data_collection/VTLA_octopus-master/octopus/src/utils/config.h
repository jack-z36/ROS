#ifndef SCANNER_CONFIG_H
#define SCANNER_CONFIG_H

#include "json.h"

#include <mcap/types.hpp>
#include <string>

namespace config
{
    inline std::string theme{ "dark" };
    inline QString     language{ "zh_CN" };
    inline QString     path{};

    namespace layout::visibility
    {
        inline bool topics_panel{ false };
    }

    namespace recording::mcap
    {
        inline std::string              path{};
        inline auto                     compression{ ::mcap::Compression::Zstd };
        inline std::vector<std::string> topics{};

    } // namespace recording::mcap

    void from_json(const json& j);
    json to_json();
} // namespace config

namespace config
{
    inline constexpr auto filename = "scanner.json";

    void load();
    void save();
} // namespace config

#endif //! SCANNER_CONFIG_H