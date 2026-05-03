#ifndef SCANNER_TITLE_BAR_H
#define SCANNER_TITLE_BAR_H

#include <QPointer>
#include <QWidget>

class QAbstractButton;
class QLabel;
class QHBoxLayout;

class TitleBar : public QWidget
{
    Q_OBJECT
public:
    explicit TitleBar(QWidget *parent);

    [[nodiscard]] virtual bool isInSystemButtons(const QPoint& pos) const;

    QWidget *addWidget(QWidget *widget, int stretch = 0, Qt::Alignment alignment = Qt::Alignment());

    void setIcon(const QIcon& icon);

    [[nodiscard]] QAbstractButton *iconButton() const;

    [[nodiscard]] QLabel *titleLabel() const;

    [[nodiscard]] QAbstractButton *pinButton() const;

    [[nodiscard]] QAbstractButton *minButton() const;

    [[nodiscard]] QAbstractButton *maxButton() const;

    [[nodiscard]] QAbstractButton *fullscreenButton() const;

    [[nodiscard]] QAbstractButton *closeButton() const;

protected:
    void mouseDoubleClickEvent(QMouseEvent *event) override;

    bool eventFilter(QObject *obj, QEvent *event) override;

    QPointer<QAbstractButton> icon_btn_{};
    QIcon                     icon_{};
    QPointer<QLabel>          title_label_{};
    QPointer<QHBoxLayout>     lhbox_{};
    QPointer<QHBoxLayout>     rhbox_{};
    QPointer<QAbstractButton> pin_btn_{};
    QPointer<QAbstractButton> min_btn_{};
    QPointer<QAbstractButton> max_btn_{};
    QPointer<QAbstractButton> full_btn_{};
    QPointer<QAbstractButton> close_btn_{};
};
#endif //! SCANNER_TITLE_BAR_H
