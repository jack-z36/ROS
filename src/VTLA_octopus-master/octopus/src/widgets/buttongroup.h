#ifndef SCANNER_BUTTON_GROUP_H
#define SCANNER_BUTTON_GROUP_H

#include <QAbstractButton>

class ButtonGroup final : public QObject
{
    Q_OBJECT
public:
    explicit ButtonGroup(QObject *parent) : QObject(parent){}

    void addButton(QAbstractButton *button);

signals:
    void emptied();

private:
    QVector<QAbstractButton *> buttons_{};
};

#endif //! SCANNER_BUTTON_GROUP_H