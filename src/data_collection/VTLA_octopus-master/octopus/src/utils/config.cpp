#include "config.h"

#include <QFile>
#include <QIODeviceBase>
#include <QStandardPaths>
#include <QTextStream>

#define JSON_GET(V, J, KEY)                                                                                \
    if ((J).contains(KEY)) (V) = (J)[KEY].get<decltype(V)>()

namespace config
{
    void from_json(const json& j)
    {
        JSON_GET(language, j, "language");
        JSON_GET(theme, j, "theme");

        if (j.contains("recording")) {
            if (j["recording"].contains("mcap")) {
                JSON_GET(recording::mcap::path, j["recording"]["mcap"], "path");
                JSON_GET(recording::mcap::compression, j["recording"]["mcap"], "compression");
                JSON_GET(recording::mcap::topics, j["recording"]["mcap"], "topics");
            }
        }
    }

    json to_json()
    {
        json j;

        j["language"] = language;
        j["theme"]    = theme;

        j["recording"]["mcap"]["path"]        = recording::mcap::path;
        j["recording"]["mcap"]["compression"] = recording::mcap::compression;
        j["recording"]["mcap"]["topics"]      = recording::mcap::topics;

        return j;
    }
} // namespace config

namespace config
{
    void load()
    {
        path = QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation) + "/" + filename;
        // load configure file
        QString text;
        QFile   file(path);
        if (file.open(QIODevice::ReadWrite | QIODevice::Text)) {
            QTextStream in(&file);
            text = in.readAll();
        }

        // parse json string
        try {
            from_json(json::parse(text.toStdString()));
        }
        catch (json::parse_error&) {
        }

        if (recording::mcap::path.empty()) {
            recording::mcap::path =
                QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation).toStdString();
        }

        if (recording::mcap::topics.empty()) {
            recording::mcap::topics = {
                "/baton_mini_right/fast_odom",
                "/baton_mini_left/fast_odom",
                "/gopro_right/image_raw",
                "/gopro_left/image_raw",
                "/pressure/left_hand/gripper_1",
                "/pressure/left_hand/gripper_2",
                "/pressure/right_hand/gripper_1",
                "/pressure/right_hand/gripper_2",
            };
        }
    }

    void save()
    {
        QFile file(path);

        if (!file.open(QIODevice::ReadWrite | QIODevice::Truncate | QIODevice::Text)) return;

        QTextStream out(&file);
        out << to_json().dump(4).c_str();

        file.close();
    }
} // namespace config
