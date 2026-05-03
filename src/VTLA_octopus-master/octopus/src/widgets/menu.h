#ifndef SCANNER_MENU_H
#define SCANNER_MENU_H

#include <QMenu>

class Menu final : public QMenu
{
    Q_OBJECT
public:
    explicit Menu(QWidget *parent = nullptr);
    explicit Menu(const QString& title, QWidget *parent = nullptr);

private:
#ifdef Q_OS_WIN
    bool eventFilter(QObject *watched, QEvent *event) override;
#endif
};

#endif // !SCANNER_MENU_H