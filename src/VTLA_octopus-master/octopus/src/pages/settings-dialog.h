#ifndef SCANNER_SETTINGS_DIALOG_H
#define SCANNER_SETTINGS_DIALOG_H

#include <QDialog>

class QListWidget;
class QStackedWidget;

class SettingsDialog final : public QDialog
{
    Q_OBJECT
public:
    explicit SettingsDialog(QWidget *parent = nullptr);

protected:
    void closeEvent(QCloseEvent *) override;

private:
    QWidget *GeneralPage();
    QWidget *RecordPage();
    QWidget *AboutPage();

    QListWidget    *menu_{};
    QStackedWidget *stack_{};
};

#endif //! SCANNER_SETTINGS_DIALOG_H