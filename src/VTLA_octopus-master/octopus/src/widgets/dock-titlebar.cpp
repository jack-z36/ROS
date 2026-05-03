#include "dock-titlebar.h"

#include "dock-widget.h"

#include <QCheckBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QStyle>

DockTitleBar::DockTitleBar(DockWidget *parent) : TitleBar(dynamic_cast<QWidget *>(parent))
{
    layout()->setContentsMargins({ 0, 0, 0, 1 });

    icon_btn_->hide();
    min_btn_->hide();
    max_btn_->hide();
    full_btn_->hide();

    connect(parent, &DockWidget::topLevelChanged, [=, this](const bool floating) {
        max_btn_->setVisible(floating);
        max_btn_->setChecked(qobject_cast<QWidget *>(parent)->isMaximized());
    });
}
