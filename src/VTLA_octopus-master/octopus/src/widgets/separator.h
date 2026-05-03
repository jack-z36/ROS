#ifndef SCANNER_SEPARATOR_H
#define SCANNER_SEPARATOR_H

#include <QFrame>

class Separator final : public QFrame
{
public:
    explicit Separator(QWidget *parent = nullptr);
    explicit Separator(Shape shape, int len, QWidget *parent = nullptr);
};

#endif //! SCANNER_SEPARATOR_H
