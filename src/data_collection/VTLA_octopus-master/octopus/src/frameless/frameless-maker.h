#ifndef SCANNER_FRAMELESS_MAKER_H
#define SCANNER_FRAMELESS_MAKER_H

#include "titlebar.h"

#include <QAbstractNativeEventFilter>
#include <QWidget>

class FramelessMaker final : public QObject
#ifdef Q_OS_WIN
    ,
                             public QAbstractNativeEventFilter
#endif
{
    Q_OBJECT
public:
    explicit FramelessMaker(QWidget *parent);

    explicit FramelessMaker(TitleBar *bar, QWidget *parent);

    ~FramelessMaker() override;

    void setup(QWidget *win);

    void setup(QWidget *win, TitleBar *bar);

    [[nodiscard]] QWidget  *win() const { return win_; }
    [[nodiscard]] TitleBar *titlebar() const { return titlebar_; }

#ifdef Q_OS_WIN
    bool nativeEventFilter(const QByteArray& eventType, void *message, qintptr *result) override;
#endif

protected:
    bool eventFilter(QObject *watched, QEvent *event) override;

private:
    QWidget *win_{};
#ifdef Q_OS_WIN
    HWND hwnd_{};
#elifdef Q_OS_LINUX
    Qt::Edges edges_{};
    void      updateCursor(Qt::Edges edges);
#endif
    TitleBar *titlebar_{};
};

#endif //! SCANNER_FRAMELESS_MAKER_H
