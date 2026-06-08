#include "buttongroup.h"

void ButtonGroup::addButton(QAbstractButton *button)
{
    button->setCheckable(true);
    buttons_.push_back(button);

    connect(button, &QAbstractButton::clicked, [=, this](bool state) {
        for (auto& btn : buttons_) {
            if (btn != button) btn->setChecked(false);
        }

        if (!state) emit emptied();
    });
}
