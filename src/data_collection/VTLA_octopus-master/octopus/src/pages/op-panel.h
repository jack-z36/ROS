#ifndef SCANNER_OP_WINDOW_H
#define SCANNER_OP_WINDOW_H

#include "widgets/dock-widget.h"

class QListWidget;
class QLabel;
class McapRecorder;
class QTimer;

class OpDockWidget final : public DockWidget
{
    Q_OBJECT
public:
    explicit OpDockWidget(const QString& title, QWidget *parent = nullptr,
                          Qt::WindowFlags flags = Qt::WindowFlags());

    void start();
    void stop();

private:
    QPointer<QLabel>      time_label_{};
    QPointer<QListWidget> list_{};

    std::shared_ptr<McapRecorder> recorder_{};
    QPointer<QTimer>              timer_{};
};

#endif //! SCANNER_OP_WINDOW_H