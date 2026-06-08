#include "scanner.h"

#include "utils/config.h"
#include "utils/logging.h"

#include <QFile>
#include <QFontDatabase>
#include <QIcon>
#include <QStyleFactory>
#include <QTranslator>

Scanner::Scanner(int& argc, char **argv)
    : QApplication(argc, argv)
{
    setWindowIcon(QIcon{ ":/icons/scanner" });

    // config
    config::load();

    // fonts
    QFontDatabase::addApplicationFont(":/fonts/agave");
    QFontDatabase::addApplicationFont(":/fonts/agave-bold");

    // theme
    setStyle(QStyleFactory::create("Fusion"));

    LoadTheme(config::theme);

    // language
    translator_ = new QTranslator(this);
    if (const auto file = qApp->applicationDirPath() + "/translations/scanner_" + config::language;
        !translator_->load(file))
        LOG_E("failed to load '{}'", file.toStdString());

    installTranslator(translator_);
}

bool Scanner::event(QEvent *event)
{
    if (event->type() == QEvent::ThemeChange) {
        LoadTheme(config::theme);
        return true;
    }

    if (event->type() == QEvent::Quit) {
        config::save();
    }

    return QApplication::event(event);
}

void Scanner::LoadTheme(const std::string& theme)
{
    const std::vector<QString> files{
        ":/stylesheets/fluent",
        ":/stylesheets/fluent-" + QString::fromStdString(theme),
        ":/stylesheets/scanner",
        ":/stylesheets/scanner-" + QString::fromStdString(theme),
    };

    QString style{};
    for (auto& qss : files) {
        if (QFile file(qss); file.open(QFile::ReadOnly)) {
            style += file.readAll();
            file.close();
        }
    }
    qApp->setStyleSheet(style);

    QIcon::setThemeName(QString::fromStdString(theme));

    App()->StyleChanged();
}