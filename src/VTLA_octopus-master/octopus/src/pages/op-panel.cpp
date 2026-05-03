#include "op-panel.h"

#include "mcap-recorder.h"
#include "utils/config.h"
#include "widgets/message.h"

#include <QLabel>
#include <QListWidget>
#include <QListWidgetItem>
#include <QPushButton>
#include <QSizePolicy>
#include <QTimer>
#include <QVBoxLayout>
#include <spdlog/fmt/chrono.h>

#include <algorithm>
#include <vector>

OpDockWidget::OpDockWidget(const QString& title, QWidget *parent, const Qt::WindowFlags flags)
    : DockWidget(title, parent, flags)
{
    setMaximumWidth(360);

    time_label_ = new QLabel("00:00", this);
    time_label_->setAlignment(Qt::AlignCenter);
    time_label_->setMargin(20);
    time_label_->setObjectName("time-label");
    layout_->addWidget(time_label_);

    list_ = new QListWidget();
    list_->setUniformItemSizes(true);
    list_->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    list_->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    layout_->addWidget(list_, 1);
    for (const auto& topic : config::recording::mcap::topics) {
        const auto item = new QListWidgetItem(QString::fromStdString(topic), list_);
        item->setFlags(item->flags() | Qt::ItemIsUserCheckable);
        item->setCheckState(Qt::Checked);
    }
    const auto visible_rows = std::max(8, list_->count());
    list_->setMinimumHeight(visible_rows * 30 + 2 * list_->frameWidth());

    const auto hbox = new QHBoxLayout();
    hbox->setContentsMargins({ 20, 20, 20, 20 });
    hbox->setSpacing(20);
    layout_->addLayout(hbox);

    const auto cancel_button  = new QPushButton(tr("Cancel"));
    const auto control_button = new QPushButton(tr("Start"));
    control_button->setCheckable(true);
    hbox->addWidget(cancel_button);
    hbox->addWidget(control_button);

    // timer
    timer_ = new QTimer(this);
    timer_->start(500);

    connect(timer_, &QTimer::timeout, this, [this] {
        if (recorder_ && recorder_->running()) {
            time_label_->setText(fmt::format("{:%M:%S}", std::chrono::duration_cast<std::chrono::seconds>(
                                                             recorder_->duration()))
                                     .c_str());
        }
    });
    connect(control_button, &QPushButton::clicked, [=, this](const bool checked) {
        if (checked) {
            start();
        }
        else {
            stop();
        }
        const auto recording = recorder_ && recorder_->running();
        control_button->setChecked(recording);
        control_button->setText(recording ? tr("Stop") : tr("Start"));
    });
}

void OpDockWidget::start()
{
    std::vector<std::string> topics;
    for (int i = 0; i < list_->count(); ++i) {
        const auto item = list_->item(i);
        if (item->checkState() == Qt::Checked) {
            topics.emplace_back(item->text().toStdString());
        }
    }
    if (topics.empty()) {
        Message::error(this, tr("no topic selected"));
        return;
    }

    recorder_ = std::make_shared<McapRecorder>();
    recorder_->subscribe_topics(topics);
    const auto filename =
        fmt::format("{}/{:%F_%T}.mcap", config::recording::mcap::path, std::chrono::system_clock::now());
    if (recorder_->record(filename, config::recording::mcap::compression) <0) {
        Message::error(this, tr("failed to record the topics"));
    }
}

void OpDockWidget::stop() { recorder_.reset(); }
