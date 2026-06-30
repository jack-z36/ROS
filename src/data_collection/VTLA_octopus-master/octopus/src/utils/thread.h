#ifndef PROBE_THREAD_H
#define PROBE_THREAD_H

#include <cstdint>
#include <string>

namespace probe::thread
{
    // linux: The thread name is a meaningful C language string, whose length is
    //        restricted to 16 characters, including the terminating null byte ('\0')
    int set_name(const std::string&);

    // get name of specific thread
    std::string name(uint64_t);

    // get name of the current thread
    std::string name();
} // namespace probe::thread

#endif //! PROBE_THREAD_H