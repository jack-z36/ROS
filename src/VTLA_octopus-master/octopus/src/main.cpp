#include "mainwindow.h"
#include "scanner.h"
#include "utils/defer.h"
#include "utils/logging.h"

int main(int argc, char **argv)
{
    Logger::init(argv[0], "");

    // ros2
    rclcpp::InitOptions options{};
    options.auto_initialize_logging(false);
    rclcpp::init(argc, argv, options);
    defer(rclcpp::shutdown());

    // qt application
    Scanner app(argc, argv);

    const auto window = new MainWindow();
    window->show();

    return Scanner::exec();
}