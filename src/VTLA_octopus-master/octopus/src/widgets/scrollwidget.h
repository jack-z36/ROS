#ifndef SCANNER_SCROLL_WIDGET_H
#define SCANNER_SCROLL_WIDGET_H

#include <QPointer>
#include <QScrollArea>

class QFormLayout;
class QVBoxLayout;

class ScrollWidget : public QScrollArea
{
    Q_OBJECT

public:
    explicit ScrollWidget(QWidget *parent = nullptr);

    QFormLayout *addForm(const QString& label);

    void addSpacer();

private:
    QPointer<QWidget>     widget_{};
    QPointer<QVBoxLayout> layout_{};
};

#endif //! SCANNER_SCROLL_WIDGET_H