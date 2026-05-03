#ifndef SCANNER_MESSAGE_H
#define SCANNER_MESSAGE_H

#include <QTimer>
#include <QWidget>

class Message final : public QWidget
{
    Q_OBJECT

public:
    enum class MessageLevel
    {
        LEVEL_MESSAGE,
        LEVEL_SUCCESS,
        LEVEL_WARNING,
        LEVEL_ERROR,
    };

public:
    Message(const QString& text, MessageLevel level, QWidget *parent = nullptr);

    static void message(QWidget *parent, const QString& text);
    static void success(QWidget *parent, const QString& text);
    static void warning(QWidget *parent, const QString& text);
    static void error(QWidget *parent, const QString& text);

private:
    QTimer timer_;
};

#endif // !SCANNER_MESSAGE_H