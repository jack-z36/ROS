#ifndef SCANNER_NAVIGATION_BAR_H
#define SCANNER_NAVIGATION_BAR_H

#include <QWidget>

class QButtonGroup;
class QAbstractButton;

class NavigationBar final : public QWidget
{
    Q_OBJECT

public:
    explicit NavigationBar(QWidget *parent = nullptr);

    void add(QAbstractButton *button, int id = -1);

    void addStretch(int stretch = 0);

    [[nodiscard]] int id() const;
    void              setId(int id);

signals:
    void toggled(int);

private:
    QButtonGroup *group_{};
};

#endif //! SCANNER_NAVIGATION_BAR_H