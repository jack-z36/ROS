#include "topics-widget.h"

#include "widgets/dock-titlebar.h"

#include <QListWidget>
#include <QToolButton>
#include <QVBoxLayout>

TopicsDockWidget::TopicsDockWidget(const QString& title, QWidget *parent, const Qt::WindowFlags flags)
    : DockWidget(title, parent, flags)
{
    setMinimumHeight(160);

    list_panel_ = new QListWidget();
    layout_->addWidget(list_panel_);

    // refresh
    const auto refresh_action = new QAction(QIcon::fromTheme("refresh"), tr("Refresh"));
    const auto refresh_button = new QToolButton();
    refresh_button->setDefaultAction(refresh_action);

    titlebar_->addWidget(refresh_button, 0, Qt::AlignRight);

    connect(refresh_action, &QAction::triggered, this, &TopicsDockWidget::refresh);
    connect(this, &TopicsDockWidget::aliveChanged, this, &TopicsDockWidget::refresh);
}

void TopicsDockWidget::update(const std::map<std::string, std::vector<std::string>>& topics) const
{
    list_panel_->clear();
    for (const auto& k : topics | std::views::keys) {
        list_panel_->addItem(QString::fromStdString(k));
    }
}
