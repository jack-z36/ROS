#ifndef SCANNER_DOCK_WIDGET_H
#define SCANNER_DOCK_WIDGET_H

#include <QDockWidget>
#include <QPointer>

class QVBoxLayout;
class FramelessMaker;
class DockTitleBar;

class DockWidget : public QDockWidget
{
    Q_OBJECT
public:
    explicit DockWidget(const QString& title, QWidget *parent = nullptr,
                        Qt::WindowFlags flags = Qt::WindowFlags());

    [[nodiscard]] bool alive() const { return alive_; }

signals:
    void aliveChanged(bool); // shown or closed

public slots:
    void setAlive(bool); // show() or close()

protected:
    void showEvent(QShowEvent *event) override;
    void closeEvent(QCloseEvent *event) override;

    QVBoxLayout             *layout_{};
    QPointer<DockTitleBar>   titlebar_{};
    QPointer<FramelessMaker> frameless_{};
    bool                     alive_{ false };
};

#endif //! SCANNER_DOCK_WIDGET_H