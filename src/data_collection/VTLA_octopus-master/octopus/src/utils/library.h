#ifndef PROBE_LIBRARY_H
#define PROBE_LIBRARY_H

#include <memory>
#include <string>

namespace probe::library
{
    struct library_t
    {
        std::string name{};
        void       *handle{};

        ~library_t();
    };

    std::shared_ptr<library_t> load(const std::string&);

    void *address_of(const std::shared_ptr<library_t>&, const std::string&);
} // namespace probe::library

#endif //! PROBE_LIBRARY_H