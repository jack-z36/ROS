#ifndef SCANNER_VIDEO_TEXTURE_WIDGET_H
#define SCANNER_VIDEO_TEXTURE_WIDGET_H

#include "media/ffmpeg-wrapper.h"
#include "media/media.h"
#include "texture-helper.h"

#include <memory>
#include <QRhiWidget>
#include <rhi/qrhi.h>
#include <vector>

class TextureWidget final : public QRhiWidget
{
    Q_OBJECT
public:
    explicit TextureWidget(QWidget *parent = nullptr);

    [[nodiscard]] QSize renderSize() const { return render_sz_; }

    void present(const av::frame& frame);

    static AVPixelFormat format(AVPixelFormat, AVPixelFormat = av::texture_formats()[0]);

signals:
    void updateRequest();

private:
    void initialize(QRhiCommandBuffer *cb) override;

    void render(QRhiCommandBuffer *cb) override;

    void create();
    void upload(QRhiResourceUpdateBatch *rub, const QMatrix4x4& mvp);

    std::mutex mtx_;

    QRhi *rhi_{};

    std::unique_ptr<QRhiGraphicsPipeline>       pipeline_{};
    std::unique_ptr<QRhiBuffer>                 vbuf_{};
    std::unique_ptr<QRhiBuffer>                 ubuf_{};
    std::unique_ptr<QRhiSampler>                sampler_{};
    std::unique_ptr<QRhiShaderResourceBindings> srb_{};
    std::vector<std::unique_ptr<QRhiTexture>>   planes_{};

    QMatrix4x4 mvp_{};

    av::vformat_t fmt_{ .pix_fmt = AV_PIX_FMT_YUV420P };
    av::frame     frame_{};
    av::frame     frame_slots_[4]{};

    std::atomic<bool> uploaded_{};
    std::atomic<bool> created_{};

    QSize image_sz_{};
    QSize render_sz_{};
};

#endif //! SCANNER_VIDEO_TEXTURE_WIDGET_H