#include "dock-widget.h"

#include "dock-titlebar.h"
#include "frameless/frameless-maker.h"

#include <QVBoxLayout>

DockWidget::DockWidget(const QString& title, QWidget *parent, Qt::WindowFlags flags)
    : QDockWidget(title, parent, flags)
{
    setMinimumWidth(240);

    setContentsMargins({});
    layout()->setSpacing(0);
    layout()->setContentsMargins({});

    titlebar_ = new DockTitleBar(this);
    setTitleBarWidget(titlebar_);

    const auto container = new QWidget();
    setContentsMargins({});
    setWidget(container);

    layout_ = new QVBoxLayout();
    layout_->setContentsMargins({});
    layout_->setSpacing(0);
    container->setLayout(layout_);

    connect(this, &DockWidget::aliveChanged, [this](auto&& state) { alive_ = state; });
}

void DockWidget::setAlive(const bool alive)
{
    if (alive)
        show();
    else
        close();
}

void DockWidget::showEvent(QShowEvent *event)
{
    emit aliveChanged(true);
    QDockWidget::showEvent(event);
}

void DockWidget::closeEvent(QCloseEvent *event)
{
    emit aliveChanged(false);
    QDockWidget::closeEvent(event);
}
