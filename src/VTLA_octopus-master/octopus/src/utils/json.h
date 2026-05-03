#ifndef SCANNER_JSON_H
#define SCANNER_JSON_H

#include <nlohmann/json.hpp>
#include <QKeySequence>

using json = nlohmann::json;

// clang-format off
inline void from_json(const json& j, QString& qstr)         { qstr = QString::fromStdString(j.get<std::string>()); }
inline void to_json(json& j, const QString& qstr)           { j = qstr.toStdString(); }

inline void from_json(const json& j, QKeySequence& key)     { key = { j.get<QString>() }; }
inline void to_json(json& j, const QKeySequence& key)       { j = key.toString(); }

// clang-format on

#endif //! SCANNER_JSON_H
