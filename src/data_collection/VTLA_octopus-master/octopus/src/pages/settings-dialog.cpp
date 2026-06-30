#include "settings-dialog.h"

#include "frameless/frameless-maker.h"
#include "frameless/titlebar.h"
#include "scanner.h"
#include "utils/config.h"
#include "version.h"
#include "widgets/combobox.h"
#include "widgets/path-edit.h"
#include "widgets/scrollwidget.h"

#include <QCheckBox>
#include <QCoreApplication>
#include <QFormLayout>
#include <QLabel>
#include <QLineEdit>
#include <QListWidget>
#include <QPlainTextEdit>
#include <QStackedWidget>
#include <spdlog/fmt/ranges.h>

SettingsDialog::SettingsDialog(QWidget *parent)
    : QDialog(parent)
{
    setMinimumSize(640, 480);

    const auto titlebar = new TitleBar(this);
    new FramelessMaker(titlebar, this);

    const auto layout = new QVBoxLayout();
    layout->setSpacing(0);
    layout->setContentsMargins({});
    setLayout(layout);

    setWindowTitle(tr("Settings"));
    layout->addWidget(titlebar);

    const auto hbox = new QHBoxLayout();
    layout->addLayout(hbox);

    menu_  = new QListWidget();
    stack_ = new QStackedWidget();
    hbox->addWidget(menu_);
    hbox->addWidget(stack_);

    titlebar->titleLabel()->setFixedWidth(175);
    menu_->setFixedWidth(175);
    menu_->setFocusPolicy(Qt::NoFocus);

    menu_->addItem(tr("General"));
    menu_->addItem(tr("Data Storage"));
    menu_->addItem(tr("About"));

    stack_->addWidget(GeneralPage());
    stack_->addWidget(RecordPage());
    stack_->addWidget(AboutPage());

    connect(menu_, &QListWidget::currentRowChanged, stack_, &QStackedWidget::setCurrentIndex);

    menu_->setCurrentRow(0);
}

void SettingsDialog::closeEvent(QCloseEvent *event)
{
    config::save();
    QDialog::closeEvent(event);
}

static QLabel *LABEL(const QString& text, const int width)
{
    const auto label = new QLabel(text);
    label->setMinimumWidth(width);
    return label;
}

QWidget *SettingsDialog::GeneralPage()
{
    const auto page = new ScrollWidget();
    {
        const auto form = page->addForm(tr("General"));

        const auto theme = new ComboBox({
            { "dark", tr("Dark") },
            { "light", tr("Light") },
        });
        theme->select(config::theme);
        theme->onselected([](auto&& value) {
            config::theme = value.toString().toStdString();

            QEvent event{ QEvent::ThemeChange };
            QApplication::sendEvent(qApp, &event);
        });

        form->addRow(LABEL(tr("Theme"), 125), theme);

        const auto lang = new ComboBox({
            { "en_US", "English" },
            { "zh_CN", "中文简体" },
        });
        lang->select(config::language);
        lang->onselected([](auto&& value) { config::language = value.toString(); });
        form->addRow(LABEL(tr("Language"), 125), lang);

        const auto path = new QLineEdit(config::path);
        path->setReadOnly(true);
        path->setContextMenuPolicy(Qt::NoContextMenu);
        form->addRow(LABEL(tr("Configuration File"), 125), path);
    }

    page->addSpacer();

    return page;
}

QWidget *SettingsDialog::RecordPage()
{
    const auto page = new ScrollWidget();
    {
        const auto form = page->addForm("Mcap");

        const auto path = new PathEdit(QString::fromStdString(config::recording::mcap::path));
        connect(path, &PathEdit::changed,
                [](auto&& dir) { config::recording::mcap::path = dir.toStdString(); });
        form->addRow(LABEL(tr("Save Path"), 125), path);

        const auto format = new ComboBox();
        format->add({ { 0, "None" }, { 2, "Zstandard" } })
            .onselected([](const auto& value) {
                config::recording::mcap::compression = static_cast<mcap::Compression>(value.toInt());
            })
            .select(2);
        form->addRow(tr("Compression"), format);

        const auto topics = new QPlainTextEdit();
        topics->setReadOnly(true);
        topics->setPlainText(fmt::format("{}", fmt::join(config::recording::mcap::topics, ",\n")).c_str());
        form->addRow(tr("Topics"), topics);
    }

    page->addSpacer();

    return page;
}

QWidget *SettingsDialog::AboutPage()
{
    const auto page = new QWidget();
    const auto vbox = new QVBoxLayout();

    {
        vbox->addStretch(1);

        // logo
        {
            const auto hbox = new QHBoxLayout();
            vbox->addLayout(hbox);

            hbox->addStretch();

            const auto icon = new QLabel();
            icon->setScaledContents(true);
            icon->setFixedSize(100, 100);
            icon->setPixmap(QPixmap(":/icons/scanner"));
            icon->setAlignment(Qt::AlignCenter);

            hbox->addWidget(icon);

            hbox->addStretch();
        }

        const auto name = new QLabel(tr("Octopus"));
        name->setAlignment(Qt::AlignCenter);
        name->setObjectName("about-name");
        vbox->addWidget(name);

        const auto version = new QLabel("Version : " + QString(OCTOPUS_VERSION));
        version->setAlignment(Qt::AlignCenter);
        version->setObjectName("about-version");
        vbox->addWidget(version);

        vbox->addStretch(2);

        const auto copyright =
            new QLabel("Copyright © 武汉华威科智能技术有限公司 · 版权所有\n"
                       "武汉市东湖新技术开发区高新大道999号武汉未来科技城龙山创新园C3栋1301-1、1401");
        copyright->setAlignment(Qt::AlignCenter);
        copyright->setObjectName("copyright");
        vbox->addWidget(copyright);
    }
    page->setLayout(vbox);

    return page;
}