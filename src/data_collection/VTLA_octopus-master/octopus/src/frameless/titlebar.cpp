#include "titlebar.h"

#include <QCheckBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QMouseEvent>
#include <QPushButton>
#include <QShortcut>
#include <QStyle>
#include <QWindow>

#ifdef Q_OS_WIN
#include <dwmapi.h>
#include <windowsx.h>
#endif

static void SetWindowStayOnTop(QWidget *win, bool top = true)
{
    if (!win || !win->winId()) return;

#ifdef Q_OS_WIN
    ::SetWindowPos(reinterpret_cast<HWND>(win->winId()), top ? HWND_TOPMOST : HWND_NOTOPMOST, 0, 0, 0, 0,
                   SWP_NOMOVE | SWP_NOSIZE);
#else
    win->setWindowFlag(Qt::WindowStaysOnTopHint, top);
    win->show();
#endif
}

TitleBar::TitleBar(QWidget *parent)
    : QWidget(parent)
{
    setAttribute(Qt::WA_StyledBackground);
    setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);

    const auto layout = new QHBoxLayout(this);
    layout->setSpacing(0);
    layout->setContentsMargins({});

    // icon
    icon_btn_ = new QPushButton();
    icon_btn_->setAttribute(Qt::WA_TransparentForMouseEvents);
    icon_btn_->setObjectName("icon");
    icon_btn_->setIcon(parent->windowIcon());
    layout->addWidget(icon_btn_, 0, Qt::AlignCenter);

    // title
    title_label_ = new QLabel(parent->windowTitle());
    title_label_->setObjectName("title");
    layout->addWidget(title_label_);

    // blank
    lhbox_ = new QHBoxLayout();
    lhbox_->setSpacing(0);
    lhbox_->setContentsMargins({});
    layout->addLayout(lhbox_);

    layout->addStretch();

    rhbox_ = new QHBoxLayout();
    rhbox_->setSpacing(0);
    rhbox_->setContentsMargins({});
    layout->addLayout(rhbox_);

    // pin button
    if (parent->windowFlags() & Qt::WindowStaysOnTopHint) {
        pin_btn_ = new QCheckBox(this);
        pin_btn_->setContextMenuPolicy(Qt::PreventContextMenu);
        pin_btn_->setObjectName("pin-btn");
        pin_btn_->setCheckable(true);
        pin_btn_->setChecked(parent->windowFlags() & Qt::WindowStaysOnTopHint);
        connect(pin_btn_, &QCheckBox::toggled,
                [parent](auto checked) { SetWindowStayOnTop(parent, checked); });
        layout->addWidget(pin_btn_, 0, Qt::AlignTop | Qt::AlignRight);
    }

    // minimize button
    if (parent->windowFlags() & Qt::WindowMinimizeButtonHint) {
        min_btn_ = new QCheckBox(this);
        min_btn_->setContextMenuPolicy(Qt::PreventContextMenu);
        min_btn_->setObjectName("min-btn");
        min_btn_->setCheckable(false);
        connect(min_btn_, &QCheckBox::clicked, parent, &QWidget::showMinimized);
        layout->addWidget(min_btn_, 0, Qt::AlignTop | Qt::AlignRight);
    }

    // maximize button
    if (parent->windowFlags() & Qt::WindowMaximizeButtonHint) {
        max_btn_ = new QCheckBox(this);
        max_btn_->setContextMenuPolicy(Qt::PreventContextMenu);
        max_btn_->setObjectName("max-btn");
        max_btn_->setCheckable(true);
        connect(max_btn_, &QCheckBox::clicked,
                [parent](int) { parent->isMaximized() ? parent->showNormal() : parent->showMaximized(); });
        layout->addWidget(max_btn_, 0, Qt::AlignTop | Qt::AlignRight);
    }

    // fullscreen button
    const auto toggleFullScreen = [parent] {
        parent->isFullScreen() ? parent->showNormal() : parent->showFullScreen();
    };
    if (parent->windowFlags() & Qt::WindowFullscreenButtonHint) {
        full_btn_ = new QCheckBox(this);
        full_btn_->setContextMenuPolicy(Qt::PreventContextMenu);
        full_btn_->setObjectName("full-btn");
        full_btn_->setCheckable(true);
        connect(full_btn_, &QCheckBox::clicked, toggleFullScreen);
        layout->addWidget(full_btn_, 0, Qt::AlignTop | Qt::AlignRight);
    }

    // close button
    if (parent->windowFlags() & Qt::WindowCloseButtonHint) {
        close_btn_ = new QCheckBox(this);
        close_btn_->setContextMenuPolicy(Qt::PreventContextMenu);
        close_btn_->setObjectName("close-btn");
        close_btn_->setCheckable(false);
        connect(close_btn_, &QCheckBox::clicked, parent, &QWidget::close);
        layout->addWidget(close_btn_, 0, Qt::AlignTop | Qt::AlignRight);
    }

    //
    connect(new QShortcut(Qt::Key_F11, parent), &QShortcut::activated, toggleFullScreen);

    parent->installEventFilter(this);
}

bool TitleBar::isInSystemButtons(const QPoint& pos) const
{
    return lhbox_->geometry().contains(pos) || pos.x() > rhbox_->geometry().left();
}

QAbstractButton *TitleBar::iconButton() const { return icon_btn_; }

QLabel *TitleBar::titleLabel() const { return title_label_; }

QAbstractButton *TitleBar::pinButton() const { return pin_btn_; }

QAbstractButton *TitleBar::minButton() const { return min_btn_; }

QAbstractButton *TitleBar::maxButton() const { return max_btn_; }

QAbstractButton *TitleBar::fullscreenButton() const { return full_btn_; }

QAbstractButton *TitleBar::closeButton() const { return close_btn_; }

QWidget *TitleBar::addWidget(QWidget *widget, const int stretch, const Qt::Alignment alignment)
{
    if (alignment & Qt::AlignLeft) {
        lhbox_->addWidget(widget, stretch, alignment);
    }
    else if (alignment & Qt::AlignRight) {
        rhbox_->addWidget(widget, stretch, alignment);
    }
    return widget;
}

void TitleBar::setIcon(const QIcon& icon)
{
    icon_ = icon;
    icon_btn_->setIcon(icon_);
}

void TitleBar::mouseDoubleClickEvent(QMouseEvent *)
{
    if (max_btn_) max_btn_->click();
}

bool TitleBar::eventFilter(QObject *obj, QEvent *event)
{
    if (const auto w = qobject_cast<QWidget *>(parent()); obj == w) {
        switch (event->type()) {
        case QEvent::WindowIconChange:
            if (icon_btn_) icon_btn_->setIcon(icon_.isNull() ? w->windowIcon() : icon_);
            break;
        case QEvent::WindowTitleChange:
            if (title_label_) title_label_->setText(w->windowTitle());
            break;
        case QEvent::WindowStateChange:
            if (max_btn_) max_btn_->setChecked(w->isMaximized());
            if (full_btn_) full_btn_->setChecked(w->isFullScreen());

            if (w->windowState() == Qt::WindowNoState && !isVisible()) show();
            break;
        default: break;
        }
    }

    return QWidget::eventFilter(obj, event);
}