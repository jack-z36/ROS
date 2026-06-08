#ifndef SCANNER_TOPICS_WINDOW_H
#define SCANNER_TOPICS_WINDOW_H

#include "widgets/dock-widget.h"

class QListWidget;

class TopicsDockWidget final : public DockWidget
{
    Q_OBJECT
public:
    explicit TopicsDockWidget(const QString& title, QWidget *parent = nullptr,
                              Qt::WindowFlags flags = Qt::WindowFlags());

    void update(const std::map<std::string, std::vector<std::string>>& topics) const;

signals:
    void refresh();

private:
    QPointer<QListWidget> list_panel_{};
};

#endif //! SCANNER_VIDEO_WINDOW_H