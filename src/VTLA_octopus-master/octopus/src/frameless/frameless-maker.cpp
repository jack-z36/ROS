#include "frameless-maker.h"

#include "utils/logging.h"

#include <QMouseEvent>
#include <QStyle>
#include <QWindow>

#ifdef Q_OS_WIN
#include <dwmapi.h>
#include <probe/graphics.h>
#include <probe/system.h>
#include <QAbstractEventDispatcher>
#include <QEvent>
#include <QPlatformSurfaceEvent>
#include <windowsx.h>
#endif

FramelessMaker::FramelessMaker(QWidget *parent)
    : QObject(parent)
{
    setup(parent);
}

FramelessMaker::FramelessMaker(TitleBar *bar, QWidget *parent)
    : QObject(parent)
{
    setup(parent, bar);
}

void FramelessMaker::setup(QWidget *win)
{
    win_ = win;

    win_->setAttribute(Qt::WA_DontCreateNativeAncestors);
    win_->setAttribute(Qt::WA_NativeWindow);
    win_->installEventFilter(this);

#ifdef Q_OS_WIN
    hwnd_ = reinterpret_cast<HWND>(win_->winId());

    QAbstractEventDispatcher::instance()->installNativeEventFilter(this);

    constexpr MARGINS margins = { -1, -1, -1, -1 };
    ::DwmExtendFrameIntoClientArea(hwnd_, &margins);

    // Window Styles: https://learn.microsoft.com/en-us/windows/win32/winmsg/window-styles
    ::SetWindowLong(hwnd_, GWL_STYLE, ::GetWindowLong(hwnd_, GWL_STYLE) & ~WS_SYSMENU);

    ::SetWindowPos(hwnd_, nullptr, 0, 0, 0, 0,
                   SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOOWNERZORDER |
                       SWP_FRAMECHANGED);
#endif

#ifdef Q_OS_LINUX
    win->setWindowFlags(win->windowFlags() | Qt::FramelessWindowHint);
    win->setAttribute(Qt::WA_Hover, true);
#endif
}

FramelessMaker::~FramelessMaker()
{
#ifdef Q_OS_WIN
    QAbstractEventDispatcher::instance()->removeNativeEventFilter(this);
#endif
}

void FramelessMaker::setup(QWidget *win, TitleBar *bar)
{
    titlebar_ = bar;

#ifdef Q_OS_LINUX
    titlebar_->installEventFilter(this);
#endif

    setup(win);
}

#ifdef Q_OS_WIN

bool FramelessMaker::eventFilter(QObject *, QEvent *event)
{
    if (event->type() == QEvent::PlatformSurface) {
        QAbstractEventDispatcher::instance()->removeNativeEventFilter(this);

        if (dynamic_cast<QPlatformSurfaceEvent *>(event)->surfaceEventType() !=
            QPlatformSurfaceEvent::SurfaceAboutToBeDestroyed) {
            win_->removeEventFilter(this);
            setup(win_, titlebar_);
        }
    }
    return false;
}

static bool IsSizeFixed(const QWidget *widget)
{
    if (widget->windowFlags() & Qt::MSWindowsFixedSizeDialogHint) {
        return true;
    }

    const QSize minsize = widget->minimumSize();
    const QSize maxsize = widget->maximumSize();

    return !minsize.isEmpty() && !maxsize.isEmpty() && (minsize == maxsize);
}

static bool operator==(const RECT& lhs, const RECT& rhs) noexcept
{
    return ((lhs.left == rhs.left) && (lhs.top == rhs.top) && (lhs.right == rhs.right) &&
            (lhs.bottom == rhs.bottom));
}

static std::optional<MONITORINFOEX> MonitorInfoFromWindow(HWND hwnd)
{
    if (!::IsWindow(hwnd)) return std::nullopt;

    HMONITOR hmonitor = ::MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST);

    MONITORINFOEX info = { sizeof(MONITORINFOEX) };
    if (::GetMonitorInfo(hmonitor, &info)) return info;
    return std::nullopt;
}

static bool IsFullscreen(HWND hwnd)
{
    if (!::IsWindow(hwnd)) return false;

    RECT rect = {};
    if (::GetWindowRect(hwnd, &rect) == FALSE) return false;

    const auto monitor = MonitorInfoFromWindow(hwnd);
    return monitor && (monitor->rcMonitor == rect);
}

static int ResizeHandleHeight(HWND hWnd)
{
    const auto dpi = probe::graphics::retrieve_dpi_for_window(reinterpret_cast<uint64_t>(hWnd));

    return ::GetSystemMetricsForDpi(SM_CYSIZEFRAME, dpi) + ::GetSystemMetricsForDpi(SM_CXPADDEDBORDER, dpi);
}

// [microsoft/terminal](https://github.com/microsoft/terminal/blob/main/src/cascadia/WindowsTerminal/NonClientIslandWindow.cpp)
bool FramelessMaker::nativeEventFilter(const QByteArray&, void *message, qintptr *result)
{
    const auto wm = static_cast<MSG *>(message);

    if (!wm || !result || !win_ || !::IsWindow(hwnd_) || wm->hwnd != hwnd_) return false;

    auto lParam = wm->lParam;
    auto wParam = wm->wParam;

    switch (wm->message) {
    // https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-nccalcsize
    case WM_NCCALCSIZE: {
        const auto rect = wParam ? &(reinterpret_cast<LPNCCALCSIZE_PARAMS>(lParam))->rgrc[0]
                                 : reinterpret_cast<LPRECT>(lParam);

        if (probe::system::version() >= probe::WIN_11) {
            const LONG original_top = rect->top;
            // apply the default frame for standard window frame (the resizable frame border and the frame
            // shadow) including the left, bottom and right edges.
            if (const LRESULT res = ::DefWindowProcW(hwnd_, WM_NCCALCSIZE, wm->wParam, wm->lParam);
                (res != HTERROR) && (res != HTNOWHERE)) {
                *result = static_cast<long>(res);
                return true;
            }
            // re-apply the original top for removing the top frame entirely
            rect->top = original_top;
        }

        //
        const auto monitor    = MonitorInfoFromWindow(hwnd_);
        const auto fullscreen = monitor && (monitor->rcMonitor == *rect);
        const auto maximized  = IsMaximized(hwnd_);

        // top frame
        if (maximized && !fullscreen) {
            rect->top += ResizeHandleHeight(hwnd_);
            if (probe::system::version() < probe::WIN_11) {
                rect->left   += ResizeHandleHeight(hwnd_);
                rect->right  -= ResizeHandleHeight(hwnd_);
                rect->bottom -= ResizeHandleHeight(hwnd_);
            }
        }

        // autohide taskbar
        if (maximized || fullscreen) {
            APPBARDATA abd{ .cbSize = sizeof(APPBARDATA) };

            if (const UINT taskbar_state = ::SHAppBarMessage(ABM_GETSTATE, &abd);
                taskbar_state & ABS_AUTOHIDE) {

                UINT taskbar_postion = ABE_BOTTOM;

                if (!monitor) break;

                for (const auto& abe : std::vector<UINT>{ ABE_BOTTOM, ABE_TOP, ABE_LEFT, ABE_RIGHT }) {
                    APPBARDATA pos{ .cbSize = sizeof(APPBARDATA), .uEdge = abe, .rc = monitor->rcMonitor };
                    if (::SHAppBarMessage(ABM_GETAUTOHIDEBAREX, &pos)) {
                        taskbar_postion = abe;
                        break;
                    }
                }

                switch (taskbar_postion) {
                case ABE_TOP:   rect->top += 2; break;
                case ABE_LEFT:  rect->left += 2; break;
                case ABE_RIGHT: rect->right -= 2; break;
                default:        rect->bottom -= 2; break;
                }
            }
        }

        *result = wParam ? WVR_REDRAW : FALSE;
        return true;
    }

    case WM_NCHITTEST: {
        LRESULT res = HTCLIENT;
        if (probe::system::version() >= probe::WIN_11) {
            res = ::DefWindowProcW(hwnd_, WM_NCHITTEST, 0, lParam);
            if (res == HTCLIENT) {
                RECT rect{};
                if (::GetWindowRect(hwnd_, &rect) &&
                    GET_Y_LPARAM(lParam) < rect.top + ResizeHandleHeight(hwnd_)) {
                    res = HTTOP;
                }
            }
        }
        else {
            const auto x = GET_X_LPARAM(lParam), y = GET_Y_LPARAM(lParam);
            const auto thickness = ResizeHandleHeight(hwnd_);

            RECT rect{};
            if (::GetWindowRect(hwnd_, &rect)) {
                const auto le = x > rect.left && x < (rect.left + thickness);
                const auto re = x > (rect.right - thickness) && x < rect.right;
                const auto te = y > rect.top && y < (rect.top + thickness);
                const auto be = y > (rect.bottom - thickness) && y < rect.bottom;

                if (le && te)
                    res = HTTOPLEFT;
                else if (le && be)
                    res = HTBOTTOMLEFT;
                else if (re && te)
                    res = HTTOPRIGHT;
                else if (re && be)
                    res = HTBOTTOMRIGHT;
                else if (re)
                    res = HTRIGHT;
                else if (te)
                    res = HTTOP;
                else if (le)
                    res = HTLEFT;
                else if (be)
                    res = HTBOTTOM;
            }
        }

        const auto fullscreen = IsFullscreen(hwnd_);

        if (fullscreen || IsMaximized(hwnd_) || IsSizeFixed(win_)) {
            switch (res) {
            case HTTOP:
            case HTRIGHT:
            case HTLEFT:
            case HTBOTTOM:
            case HTTOPLEFT:
            case HTTOPRIGHT:
            case HTBOTTOMLEFT:
            case HTBOTTOMRIGHT: res = HTCLIENT; break;
            default:            break;
            }
        }

        if (!fullscreen && res == HTCLIENT && titlebar_ && titlebar_->isVisible()) {
            const auto pos = win_->mapFromGlobal(QCursor::pos());
            if (titlebar_->geometry().contains(pos) && !titlebar_->isInSystemButtons(pos)) {
                *result = HTCAPTION;
                return true;
            }
        }

        *result = static_cast<long>(res);
        return true;
    }

    default: break;
    }

    return false;
}

#elif __linux__

void FramelessMaker::updateCursor(const Qt::Edges edges)
{
    switch (edges) {
    case Qt::LeftEdge:
    case Qt::RightEdge:                  win_->setCursor(Qt::SizeHorCursor); break;
    case Qt::TopEdge:
    case Qt::BottomEdge:                 win_->setCursor(Qt::SizeVerCursor); break;
    case Qt::LeftEdge | Qt::TopEdge:
    case Qt::RightEdge | Qt::BottomEdge: win_->setCursor(Qt::SizeFDiagCursor); break;
    case Qt::RightEdge | Qt::TopEdge:
    case Qt::LeftEdge | Qt::BottomEdge:  win_->setCursor(Qt::SizeBDiagCursor); break;
    default:                             win_->setCursor(Qt::ArrowCursor); break;
    }
}

bool FramelessMaker::eventFilter(QObject *obj, QEvent *event)
{
    if (obj == win_) {
        switch (event->type()) {
        case QEvent::MouseButtonPress:
            if (edges_) {
                win_->windowHandle()->startSystemResize(edges_);
                return true;
            }
            break;
        case QEvent::MouseButtonRelease: break;
        case QEvent::HoverEnter:
        case QEvent::HoverLeave:
        case QEvent::HoverMove:          {
            const auto pos = dynamic_cast<QHoverEvent *>(event)->position().toPoint();
            const auto ftn = win_->style()->pixelMetric(QStyle::PM_LayoutBottomMargin);

            edges_ = Qt::Edges{};

            if (pos.x() < ftn) edges_ |= Qt::LeftEdge;
            if (pos.x() > win_->width() - ftn) edges_ |= Qt::RightEdge;
            if (pos.y() < ftn) edges_ |= Qt::TopEdge;
            if (pos.y() > win_->height() - ftn) edges_ |= Qt::BottomEdge;

            updateCursor(edges_);
            break;
        }
        default: break;
        }
    }

    if (obj == titlebar_ && event->type() == QEvent::MouseMove &&
        !titlebar_->isInSystemButtons(reinterpret_cast<QMouseEvent *>(event)->pos())) {

        win_->windowHandle()->startSystemMove();
    }
    return false;
}

#endif
