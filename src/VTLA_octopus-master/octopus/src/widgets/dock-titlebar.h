#ifndef SCANNER_DOCK_TITLE_BAR_H
#define SCANNER_DOCK_TITLE_BAR_H

#include "frameless/titlebar.h"

class DockWidget;

class DockTitleBar final : public TitleBar
{
    Q_OBJECT

public:
    explicit DockTitleBar(DockWidget *parent);
};

#endif //! SCANNER_DOCK_TITLE_BAR_H