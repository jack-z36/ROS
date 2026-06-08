#include "chart-view.h"

#include "utils/logging.h"

ChartView::ChartView(QWidget *parent) : QChartView(parent)
{
    vline_ = new QGraphicsLineItem();
    hline_ = new QGraphicsLineItem();
    vline_->setZValue(2);
    vline_->setPen(QPen{ QColor{ 200, 200, 200 }, 1, Qt::DotLine });
    hline_->setZValue(2);
    hline_->setPen(QPen{ QColor{ 200, 200, 200 }, 1, Qt::DotLine });
    vline_->hide();
    hline_->hide();

    ylabel_ = new QGraphicsSimpleTextItem();
    ylabel_->setZValue(2);
    ylabel_->setText("0.0");
    ylabel_->hide();
    ylabel_->setPen(QPen{ QColor{ 224, 224, 224 } });
    ylabel_->setBrush(Qt::red);

    scene()->addItem(hline_);
    scene()->addItem(vline_);
    scene()->addItem(ylabel_);
}

void ChartView::enterEvent(QEnterEvent *event)
{
    vline_->setVisible(true);
    hline_->setVisible(true);
    ylabel_->setVisible(true);
    QChartView::enterEvent(event);
}

void ChartView::mouseMoveEvent(QMouseEvent *event)
{
    const auto rect = chart()->plotArea().toRect();

    const auto px = std::clamp<qreal>(event->position().x(), rect.x(), rect.width() + rect.x());
    vline_->setLine(px, rect.y(), px, rect.height() + rect.y());

    const auto py = std::clamp<qreal>(event->position().y(), rect.y(), rect.height() + rect.y());
    hline_->setLine(rect.x(), py, rect.width() + rect.x(), py);

    const auto point = chart()->mapToValue({ px, py });
    ylabel_->setText(QString("%1").arg(static_cast<int>(point.y())));
    ylabel_->setPos(QPointF(x() + 10, py - ylabel_->boundingRect().height() / 2));

    emit mouseMoved(event->position());

    QChartView::mouseMoveEvent(event);
}

void ChartView::leaveEvent(QEvent *event)
{
    vline_->setVisible(false);
    hline_->setVisible(false);
    ylabel_->setVisible(false);
    QChartView::leaveEvent(event);
}