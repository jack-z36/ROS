#include "form-dialog.h"

#include "frameless/frameless-maker.h"
#include "frameless/titlebar.h"

#include <QDialogButtonBox>
#include <QFormLayout>
#include <QVBoxLayout>

FormDialog::FormDialog(QWidget *parent)
    : QDialog(parent)
{
    const auto titlebar = new TitleBar(this);
    new FramelessMaker(titlebar, this);

    setContentsMargins({});
    setWindowModality(Qt::ApplicationModal);

    setMinimumWidth(325);

    const auto layout = new QVBoxLayout();
    layout->setSpacing(0);
    layout->setContentsMargins({});
    setLayout(layout);

    layout->addWidget(titlebar);

    form_ = new QFormLayout();
    form_->setSpacing(10);
    form_->setContentsMargins({ 15, 15, 15, 10 });
    layout->addLayout(form_);

    //
    layout->addStretch();

    const auto box = new QDialogButtonBox(this);
    box->addButton(tr("OK"), QDialogButtonBox::AcceptRole);
    box->addButton(tr("Cancel"), QDialogButtonBox::RejectRole);
    box->layout()->setSpacing(10);
    box->setContentsMargins({ 15, 10, 15, 10 });
    layout->addWidget(box);

    connect(box, &QDialogButtonBox::accepted, this, &QDialog::accept);
    connect(box, &QDialogButtonBox::rejected, this, &QDialog::reject);
}

QFormLayout *FormDialog::form() const { return form_; }
