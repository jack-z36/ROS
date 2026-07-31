# Debug 交接：左鱼眼相机模糊与 ACT 图像规格对齐

> **消费对象**：后续接手此 debug 的 Agent。
> **权威性**：本文件是本次调试的当前交接上下文；只覆盖网页控制、ACT 图像链路、左相机模糊和响应急停的结论。与运行中的真机状态冲突时，以现场的只读命令输出为准。
> **上游来源**：本次用户提供的网页截图、现场只读检查、`2026-04-30_02_00_27.248201505.mcap`、相机开发文档与当前源码。
> **不负责范围**：不授权启动/停止真机、清急停、下发机械臂动作，或改动相机 UVC 控制值。
> **读取时机**：继续排查左相机模糊、修改 ACT 图像输入规格、或恢复网页/真机启动链路前。
> **冲突处理**：先以本文件的“事实”区和现场只读检查复核；需要改 UVC 曝光/增益或接触镜头时，必须先获得用户明确授权。

## 0. 结论先行

当前有 **两个彼此独立的问题**，不能混为“左相机的模糊”。

| 问题 | 已确认程度 | 根因范围 |
| --- | --- | --- |
| 左画面比右画面明显更糊 | **已确认差异发生在原始 `/dev/video0` 采集阶段** | 左相机的自动曝光/ISP 或镜头光学状态；不是 ROS、ACT、网页单独制造的左侧差异 |
| ACT/网页的两路图像都经历不必要的缩放 | **源码已确认** | `config/repo/ui/service` 的图像 shape 配置不一致；会降低两侧细节，但不能解释只有左边更糊 |

因此下一窗口的目标顺序是：

1. 先用“同场景 + 相同手动曝光/增益”的受控对照，将左路问题定性为 **自动曝光/ISP** 或 **镜头/传感器光学**。
2. 再单独修复 ACT 的 `640×480 → 640×640 → 640×480` 双重缩放，使部署输入与训练 MCAP 对齐。

不要先改网页 CSS、JPEG 质量或 ROS QoS 来试图修复左侧单路模糊；它们无法解释原始设备层已有的左右差异。

---

## 1. 已确认的事实与证据

### 1.1 训练数据 / 模型期望的图像规格

用户提供的训练 MCAP：

```text
/media/hit/BE84424B01016691/umi数据/数据2.0/已通过健康审计文件/
2026-04-30_02_00_27.248201505.mcap
```

对 `/gopro_left/image_raw` 和 `/gopro_right/image_raw` 的全量解码统计：

| 字段 | 左 / 右相机 |
| --- | --- |
| ROS 类型 | `sensor_msgs/msg/Image` |
| 宽 × 高 | **640 × 480** |
| encoding | `rgb8` |
| step / payload | `1920` / `921600` bytes |
| 帧数 | 各 547 |
| 频率 | 约 30 FPS |

模型 bundle `/home/hit/模型权重/UMI_ACT/act_07_29/first_10min/deploy_bundle` 也明确要求：

```text
experiment_config.yaml: model_image_hw: [480, 640]   # H, W
adapter/pretrained_model/config.json: [3, 480, 640] # C, H, W
```

正确的数据链应为：

```text
相机 / ROS：HWC (480, 640, 3), rgb8
ACT RAM：   CHW (3, 480, 640), float32, [0, 1]
模型输入：  CHW (3, 480, 640), float32, [0, 1]
网页预览：  保留 640×480 的宽高比
```

### 1.2 当前真机相机配置一致

文件：`src/model_deploy/dual_fisheye_camera/config/dual_fisheye_camera.yaml`

| 项 | 左 | 右 |
| --- | --- | --- |
| 稳定设备路径 | USB `0:1` | USB `0:5` |
| 采集规格 | `640×480`, `YUYV`, `30 FPS` | 同左 |
| ROS 输出 | `rgb8` | 同左 |
| QoS | sensor_data / BEST_EFFORT | 同左 |

现场 `v4l2-ctl --all` 的只读检查也显示两路都是 `640×480 YUYV @30FPS`、USB3；可见 UVC 控制值相同：brightness 0、contrast 50、saturation 64、sharpness 50、backlight_compensation 0、auto_exposure 3、gain 16、white-balance auto。

注意：`auto_exposure=3` 表示自动曝光工作中；此时 `exposure_time_absolute=625` 是 **inactive**，不能据此断言两路实际快门相同。

### 1.3 左右差异已在原始设备层出现

在 ACT、ROS 相机节点、机械臂节点都没有运行时，直接以 OpenCV 读取 `/dev/video0`（左）和 `/dev/video2`（右），各取 24 帧静态画面，结果：

| 原始设备 | Laplacian 方差中位数 | 灰度均值 |
| --- | ---: | ---: |
| 左 `/dev/video0` | **419.34**（范围 417.44–422.79） | 124.52 |
| 右 `/dev/video2` | **1921.45**（范围 1906.05–1952.16） | 97.31 |

解释边界：Laplacian 方差是清晰度的辅助量，不是绝对的焦距证明；两路看见的场景不同，数值不能单独证明镜头失焦。它足以证明：**左/右清晰度差在原始采集画面中已存在**，所以并非由 ROS、ACT、网页 JPEG 或浏览器单独造成。

### 1.4 相机文档可支持的判断

文件：`DOCS/01_知识/阶段四：模型部署/硬件开发文档/相机开发/触发-方案.md`。

| 文档事实 | 当前含义 |
| --- | --- |
| `backlight_compensation=0` 为连续出流 | 当前两路都在连续模式，不是触发漏帧 |
| 自动曝光时 DSP 自行控制曝光；手动曝光要先关闭自动曝光 | 当前两路即使配置表“相同”，实际快门/ISP 仍可能因各自取景的亮度不同而不同 |
| 自动曝光下增益设置无效 | 不能只改 gain 做诊断 |

现场 `v4l2-ctl --list-ctrls-menus` 未发现 `focus_auto` / `focus_absolute`，因此没有可用的 Linux 软件自动对焦控制。若手动曝光对照后左路仍糊，优先检查镜头保护膜、镜片污渍、水汽、镜头固定/焦距与相机模组。

---

## 2. 当前源码中已确认的全局图像问题（与左侧差异分开处理）

当前 `src/model_deploy/act/config_files/deploy.yaml`：

```yaml
image:
  image_size: 640
  resize_mode: resize_pad
```

但这份 scalar `image_size` 被 `repo` 层当作正方形 shape。实际数据流为：

```text
原始 ROS rgb8 HWC (480,640,3)
  └─ ui/observation_ros_adapter.py + service/image_preprocess.py
     └─ 直接 cv2.resize 成 HWC (640,640,3)       # 拉伸，resize_mode 目前未生效
        └─ RAM CHW (3,640,640)
           └─ service/lerobot_policy.py
              └─ torch.interpolate 回 CHW (3,480,640)
                 └─ ACT 模型
```

涉及文件和职责：

| 架构层 | 文件 | 事实 |
| --- | --- | --- |
| config | `act/config/schema.py` | `ImageConfig.image_size` 只有单个整数，不能表达 480×640 |
| repo | `act/repo/act_runtime_resources.py` | 把该整数建成 `(3, image_size, image_size)` |
| ui | `act/ui/observation_ros_adapter.py` | 按 `PolicyInputSpec.image_shapes` 预处理相机帧 |
| service | `act/service/image_preprocess.py` | 当前只直接 resize，未实现 `resize_pad` / `resize_crop` 的差异 |
| service | `act/service/lerobot_policy.py` | 预测前再插值为模型的 480×640 |
| runtime | `act/runtime/debug_observer.py` | 收到的是已处理的 640×640 帧，随后以 JPEG quality=70 提供网页 |

影响判断：这会损失两个相机的竖向细节、网页预览也看到了中间 shape；它是需要修的部署对齐 bug，**但不可能单独造成左清右晰**。

修复目标应是让 `PolicyInputSpec` / `ObservationRosAdapter` 直接使用 `(3,480,640)`；原始相机恰好同尺寸，因此无须 resize；模型 wrapper 也无须二次插值。不要仅把 `image_size` 改为 480 或 640——那仍无法表达非正方形 shape。

---

## 3. 左相机模糊：下一步可执行排查

### 3.1 分支和判据

```text
同一静态高对比目标、同一距离/光线
          │
          ├─ 自动曝光下左右差异
          │       │
          └─ 关闭自动曝光并给两路相同手动曝光/增益
                  │
                  ├─ 左右接近 → 自动曝光 / ISP / 取景亮度导致
                  └─ 左仍明显较糊 → 镜头/保护膜/污渍/焦距/模组问题
```

### 3.2 先做的只读复核（无需授权，不影响硬件状态）

在 **无 ROS 相机节点占用设备** 时执行。若节点在运行，只做 `v4l2-ctl --all`，不要争抢 `/dev/video*`。

```bash
# 1. 确认当前设备映射与控制状态
v4l2-ctl -d /dev/video0 --all
v4l2-ctl -d /dev/video2 --all
v4l2-ctl -d /dev/video0 --list-ctrls-menus
v4l2-ctl -d /dev/video2 --list-ctrls-menus

# 2. 确认采集格式（应均为 640×480 / YUYV / 30 FPS）
v4l2-ctl -d /dev/video0 --get-fmt-video --get-parm
v4l2-ctl -d /dev/video2 --get-fmt-video --get-parm
```

然后请现场人员让两只相机对准同一张有文字/棋盘格的平面，尽量相同距离与照明；保留两张原始帧和相同的裁剪区域。若相机安装位置不同而不能同时对准，**依次**拍同一目标，且不要在中间改灯光或焦距。

可用只读的最小采样脚本（用系统 Python 或当前环境中有 `cv2` 的 Python；不写文件）：

```bash
python3 - <<'PY'
import cv2
for name, path in [('left', '/dev/video0'), ('right', '/dev/video2')]:
    cap = cv2.VideoCapture(path, cv2.CAP_V4L2)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        print(name, 'READ_FAILED')
        continue
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    print(name, 'shape=', frame.shape,
          'lap_var=', round(cv2.Laplacian(gray, cv2.CV_64F).var(), 2),
          'mean=', round(float(gray.mean()), 2))
PY
```

### 3.3 需要用户明确授权的受控实验（不要擅自执行）

此实验会修改相机 UVC 的 `auto_exposure`、`exposure_time_absolute`、`gain`，因此属于外部硬件状态变更。获得授权后应：

1. 先完整记录两路 `--all` 输出，以便恢复；停止占用相机的 ROS 节点。
2. 按 `--list-ctrls-menus` 证实 `auto_exposure` 的 Manual 值；现场此前显示为 `1: Manual`、`3: Aperture Priority`。
3. 对两路先切 Manual，再写入 **同一个、经现场帧率确认不致过曝的** `exposure_time_absolute` 和 `gain`。
4. 两路面对同一静态高对比目标，重新采 20–30 帧并比较中心相同区域的清晰度，而不是比较不同取景的整帧。
5. 立即恢复第 1 步记录的控制值（当前预期为 `auto_exposure=3`, `gain=16`, 连续模式）。

不要把文档中 Windows `Exposure VALUE` 换算式直接套到 Linux 的 `exposure_time_absolute`。两者是不同 UVC/V4L2 接口语义；以本机 `v4l2-ctl --list-ctrls-menus` 的单位、范围和试验帧率为准。

### 3.4 根据实验结果的处置

| 实验结果 | 根因结论 | 后续动作 |
| --- | --- | --- |
| 手动相同曝光/增益后接近 | 自动曝光/ISP + 两路取景亮度差 | 为部署确定一组可复现的手动曝光/增益；将其写入相机启动配置或受控初始化脚本，并回归验证 30 FPS |
| 手动相同曝光/增益后左仍明显糊 | 非下游软件问题，优先光学/模组 | 检查左镜头保护膜、污渍、水汽、刮痕、松动/焦距；清洁后复拍；仍失败则互换相机模组/USB 口定位是模组还是接口 |
| 互换 USB 口后模糊跟着相机走 | 左相机模组/光学 | 修/换左模组 |
| 互换 USB 口后模糊留在原端口 | USB/供电/主机采集链路 | 查 USB 拓扑、带宽、供电、内核日志和该端口错误 |

物理检查与交换相机是实际硬件操作，仍需用户/现场人员授权和执行；不要由 Agent 擅自操作。

---

## 4. 已完成但与本次相机问题相邻的变更

### 网页与观测

- 图像订阅 QoS 已由 RELIABLE 改为 `qos_profile_sensor_data`，与相机 BEST_EFFORT 发布端匹配；此前 Observation 无数据的问题已处理。
- web_launcher 的阻塞等待已移出 FastAPI 事件循环，启动脚本会先报端口冲突；前端 Vue/Tailwind/ECharts 使用本地静态文件，避免 CDN 无法访问时显示 `{{ ... }}` 模板字面量。
- 网页图像增加了断线重连。`favicon.ico 404` 无关紧要。

### 动作响应急停

- 原响应校验对每个“应运动部件”要求在 2 秒内相对发布前的目标误差单调变小；离散夹爪与推理轨迹抖动会误触发。
- 当前默认部署配置 `runtime.response_motion_check_enabled: false`：**只禁用这一条“持续靠近目标”的硬急停**；缺观测、动作限幅、RM65 驱动限制、工作空间限制和人工急停仍保留。
- 该配置要在重新启动 ACT 进程后才会进入其 `/tmp/act_deploy_*.yaml` 副本；未获用户授权时不要替用户停止/重启真机。

---

## 5. 关键文件与验收边界

| 文件 | 下一步何时读取 |
| --- | --- |
| `src/model_deploy/dual_fisheye_camera/config/dual_fisheye_camera.yaml` | 核对设备路径、格式、帧率和 ROS QoS |
| `DOCS/01_知识/阶段四：模型部署/硬件开发文档/相机开发/触发-方案.md` | 设计 UVC 曝光/增益实验前 |
| `src/model_deploy/act/config_files/deploy.yaml` | 修改 ACT 图像规格或响应检查开关前 |
| `src/model_deploy/act/config/schema.py` | 将 image shape 从单整数升级为 H/W 前 |
| `src/model_deploy/act/repo/act_runtime_resources.py` | 修 `PolicyInputSpec.image_shapes` 时 |
| `src/model_deploy/act/ui/observation_ros_adapter.py` | 修 ROS 图像预处理和 shape 对齐时 |
| `src/model_deploy/act/service/image_preprocess.py` | 实现实际的 resize_pad/crop 或 no-op 对齐时 |
| `src/model_deploy/act/service/lerobot_policy.py` | 删除/约束二次 resize 时 |
| `src/model_deploy/act/runtime/debug_observer.py` | 分析网页 JPEG 预览与模型输入差异时 |

修改图像规格的验收至少应包括：

1. 单元测试断言相机 `480×640 rgb8` 进入 ACT 后是 `(3,480,640)`、float32 `[0,1]`。
2. startup preflight 不再要求 `(3,640,640)`，而与 bundle 的 `(3,480,640)` 一致。
3. wrapper 收到正确规格时不调用插值；网页预览保持 4:3。
4. dry-run 中两路 observation 持续更新，模型推理输入 shape 与 MCAP/模型配置一致。

未完成事项：尚未执行手动曝光受控实验，尚未进行镜头物理检查/交换，也尚未修改 ACT 非正方形图像规格的代码。
