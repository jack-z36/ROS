#ifndef SCANNER_LOGGING_H
#define SCANNER_LOGGING_H

#include <spdlog/spdlog.h>

class Logger
{
public:
    Logger(const Logger&)            = delete;
    Logger& operator=(const Logger&) = delete;
    Logger(Logger&&)                 = delete;
    Logger& operator=(Logger&&)      = delete;

    static Logger& init(const char *argv0, const std::string& path)
    {
        static Logger logger(argv0, path);
        return logger;
    }

    ~Logger() = default;

private:
    explicit Logger(const char *, const std::string&)
    {
        spdlog::set_pattern("%Y-%m-%d %H:%M:%S.%e %L %t -- [%24!s:%-3#]: %v");
    }
};

#define LOG_D(FMT, ...) SPDLOG_LOGGER_DEBUG(spdlog::default_logger(), FMT, ##__VA_ARGS__)
#define LOG_I(FMT, ...) SPDLOG_LOGGER_INFO(spdlog::default_logger(), FMT, ##__VA_ARGS__)
#define LOG_W(FMT, ...) SPDLOG_LOGGER_WARN(spdlog::default_logger(), FMT, ##__VA_ARGS__)
#define LOG_E(FMT, ...) SPDLOG_LOGGER_ERROR(spdlog::default_logger(), FMT, ##__VA_ARGS__)

#endif //! SCANNER_LOGGING_H
