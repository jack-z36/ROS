#ifndef SCANNER_CHART_VIEW_H
#define SCANNER_CHART_VIEW_H

#include <QtCharts>

class QGraphicsLineItem;
class QGraphicsSimpleTextItem;

class ChartView final : public QChartView
{
    Q_OBJECT
public:
    explicit ChartView(QWidget *parent = nullptr);

signals:
    void mouseMoved(const QPointF&);

protected:
    void enterEvent(QEnterEvent *event) override;
    void mouseMoveEvent(QMouseEvent *event) override;
    void leaveEvent(QEvent *event) override;

private:
    QGraphicsLineItem       *vline_{};
    QGraphicsLineItem       *hline_{};
    QGraphicsSimpleTextItem *ylabel_{};
};

#endif //! SCANNER_CHART_VIEW_H