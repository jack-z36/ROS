#ifndef SCANNER_FORM_DIALOG_H
#define SCANNER_FORM_DIALOG_H

#include <QDialog>

class QFormLayout;

class FormDialog final : public QDialog
{
    Q_OBJECT
public:
    explicit FormDialog(QWidget *parent = nullptr);

    [[nodiscard]] QFormLayout *form() const;

private:
    QFormLayout *form_{};
};

#endif //! SCANNER_FORM_DIALOG_H