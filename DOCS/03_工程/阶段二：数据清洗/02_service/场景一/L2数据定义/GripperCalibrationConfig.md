# GripperCalibrationConfig

## 定义

`GripperCalibrationConfig` 是夹爪开合提取所需的标定配置，来源于浏览器 GoPro 标定工具，用于把图像中的 marker 几何关系映射为归一化夹爪宽度。

## 所属位置

阶段二 Service 场景一，来源能力模块：[[夹爪开合配置生成]]。

## 现实代码来源

现有入口是 `src/data_clean/ui/mcap_calibration_wizard.py`。该程序会启动 HTTP 服务、打开浏览器、读取左右 GoPro live image，并把标定结果写回 YAML。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `hand` | enum | `left` 或 `right` |
| `image_topic` | string | GoPro 图像输入 topic |
| `output_topic` | string | gripper width 输出 topic |
| `aruco_dict` | string | ArUco 字典 |
| `marker_id_0`、`marker_id_1` | integer | 夹爪两侧 marker id |
| `marker_min`、`marker_max` | float | 关闭/张开状态对应的 marker 像素距离 |
| `gripper_max` | float | 物理最大开合宽度，用于追溯归一化值来源 |
| `calibration_source` | string | `browser_gopro_calibration` 或兼容旧值 |
| `calibrated_at` | string | 标定写出时间 |

## 有效性规则

- `marker_max` 必须大于 `marker_min`。
- `gripper_max` 必须大于 0。
- 左右手必须分别有独立配置，不允许复用同一个 marker 范围。
- 浏览器点击两个点生成的配置和 ArUco 自动采样生成的配置，最终都必须归一到本数据定义。

## 上游来源

- 终端启动的浏览器标定脚本。
- 左右 GoPro live image。
- 已有 YAML 写回逻辑。

## 下游消费者

- [[夹爪宽度提取]]
- [[Scene1Config]]
- [[Scene1CleanReport]]

## 相关链接

- [[GripperWidthSample]]
- [[Scene1Config]]
