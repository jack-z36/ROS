# L3 微元任务：实现夹爪宽度提取输出契约

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
功能组：service-s1-g3
L2 能力：夹爪宽度提取
L3 编号：service_s1_003
任务类别：数据计算类

## 2. 本次目标

```text
用 GripperCalibrationConfig 驱动现有 GoPro ArUco 夹爪宽度提取，确保 cleaned MCAP 中 gripper_width 输出数量和值域满足契约。
```

## 3. 本次不做

- 不生成夹爪标定配置。
- 不实现位姿转换。
- 不做场景二异常检测或补全。

## 4. 执行对象

- `src/data_clean/service/gripper_width.py`
- `src/data_clean/service/mcap_io.py`
- `src/data_clean/config/mcap_process_config.py`
- `src/data_clean/service/validator.py`
- `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/GripperWidthSample.md`

## 5. 现有程序盘点

本 L3 不是从零实现夹爪宽度提取。执行端必须先理解并复用现有实现。

### 5.1 `src/data_clean/service/gripper_width.py`

现有能力：

- 已定义 `GripperWidthAccumulator`，按单条 GoPro image stream 增量消费图像。
- 已使用 OpenCV ArUco 检测 marker。
- 已支持双 marker 直接计算：两个目标 marker 都存在时，取两个 marker center 的欧氏距离。
- 已支持单 marker 估计：只检测到一个 marker 时，用 marker 到图像中心线的水平距离乘 2。
- 已支持缺失帧补齐：前段用首个有效值、末段用最后有效值，中间缺口线性插值。
- 已输出 `GripperExtractionResult`，包含 `values`、`frame_count`、`direct_detection_frames`、`missing_frames`、`interpolated_frames`。
- 已有失败语义：无图像帧、全流无有效 marker、ArUco 字典不支持、图像 rank 不支持时抛 `GripperDetectionError`。

需要注意的现有风险：

- `_map_pixel_distance()` 目前把映射后的物理宽度裁剪为整数，再在 `finalize()` 中除以 `gripper_max` 得到归一化值；这会损失小数精度。
- `direct_detection_frames` 实际统计的是“有效样本帧”，其中包含单 marker 估计帧，不全是双 marker 直接检测帧；如果报告字段要区分 direct / single estimate，需要扩展统计。
- 当前 MCAP 只写 `std_msgs/msg/Float32`，`source_method` 不会进入 MCAP，只能进入报告或调试统计。

### 5.2 `src/data_clean/service/mcap_io.py`

现有能力：

- `_collect_stream_artifacts()` 已按 `config.gripper_streams` 创建每条 image stream 的 `GripperWidthAccumulator`。
- 遍历 MCAP 时，遇到配置中的 image topic，会解码 ROS Image，转换为 ndarray，并调用 `accumulator.consume(image)`。
- 遍历结束后会调用 `accumulator.finalize()`，并用 `codec.encode_float32(value)` 编码为 `std_msgs/msg/Float32` payload。
- `_write_output_file()` 已在复制原始 image message 后，追加写入同时间戳、同 sequence 的 gripper width message。
- 已注册 gripper output topic 的 schema 为 `std_msgs/msg/Float32`。

需要注意的现有风险：

- gripper message 是追加在对应 image message 之后，不是提前重排时间线；契约测试需要按 topic count 和时间戳验证，不应假设全局排序改变。
- 当前 output topic count 只按 `input_topic_count + len(config.gripper_streams)` 计算，后续如果同一输出 topic 被复用或写出失败，validator 必须兜底。

### 5.3 `src/data_clean/config/mcap_process_config.py`

现有能力：

- 已定义 `GripperStreamConfig`，字段包括 `image_topic`、`image_msg_type`、`output_topic`、`output_msg_type`、`aruco_dict`、`marker_id_0/1`、`marker_min/max`、`gripper_max`。
- `_build_gripper_streams()` 已从 YAML 的 `gripper_streams` 构造配置对象。
- `_validate_cross_field_rules()` 已检查：
  - image topic 唯一。
  - gripper output topic 唯一。
  - gripper output topic 与 pose output topic 不冲突。
  - image 输入类型必须是 `sensor_msgs/msg/Image`。
  - gripper 输出类型必须是 `std_msgs/msg/Float32`。
  - `marker_max > marker_min`。
  - `gripper_max > 0`。

### 5.4 `src/data_clean/service/validator.py`

现有能力：

- `validate_input_inventory()` 已检查配置中的 image topic 是否存在、是否有消息、是否只有一个 channel、schema 是否匹配。
- 已检查 gripper output topic 不得与输入 MCAP 已有 topic 冲突。
- `validate_output_contract()` 已检查 `frame_count == gripper_count`。
- `GripperTopicStats` 已能记录 `frame_count`、`gripper_count`、`missing_frames`、`interpolated_frames`。

## 6. 本 L3 的真实改造边界

本 L3 应围绕“把现有实现稳定纳入阶段二契约”做最小改造，不应重写算法。

必须优先完成：

1. 确认现有 `GripperStreamConfig` 字段与 [[GripperCalibrationConfig]] 一致；若字段缺失，只做兼容补齐。
2. 补测试覆盖 `GripperWidthAccumulator` 的双 marker、单 marker、插值、全流无 marker 失败。
3. 补测试覆盖 `mcap_io.py` gripper 输出数量、topic、时间戳和 `std_msgs/msg/Float32` schema。
4. 补测试覆盖配置非法值：`marker_max <= marker_min`、`gripper_max <= 0`。
5. 如果需要区分 direct marker 和 single marker estimate，则扩展统计字段；否则文档和报告字段不能把两者混称为 direct detection。

不应做：

1. 不重新实现 ArUco 检测。
2. 不把 gripper 输出改成物理宽度。
3. 不把浏览器标定配置生成逻辑塞进 `gripper_width.py`。
4. 不修改位姿转换代码。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：夹爪开合配置生成
上游接口定义位置：DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/GripperCalibrationConfig.md
当前 L3 期望消费的字段 / 文件 / 返回值：image_topic、output_topic、aruco_dict、marker_id_0、marker_id_1、marker_min、marker_max、gripper_max
是否存在接口冲突：如果配置生成器尚未完成，使用手写最小配置 fixture 驱动测试
如果有冲突，本次处理策略：只实现对 GripperCalibrationConfig 语义的消费，不反向修改浏览器配置生成器
```

## 8. 预期改动形态

- 左右 GoPro image frame 各自生成一个对应 gripper width message。
- 输出 topic 为 `/gopro_left/gripper_width`、`/gopro_right/gripper_width`。
- 输出消息类型为 `std_msgs/msg/Float32`。
- 输出值为归一化 `[0, 1]`。
- 全流无有效 marker 时失败；部分帧缺 marker 时按现有策略插值并记录统计。

## 9. 验收重点

- 双 marker、单 marker 估计、无 marker 插值都有测试。
- `marker_max <= marker_min` 配置会失败。
- gripper message count 等于对应 image frame count。
- 不输出物理宽度替代归一化值。
- 如保留整数映射，需要明确这是现有行为；如改为 float 精度，需要补回归测试证明输出仍在 `[0, 1]`。

## 10. 必读上下文

1. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/夹爪宽度提取.md`
2. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/GripperWidthSample.md`
3. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/GripperCalibrationConfig.md`
4. `src/data_clean/service/gripper_width.py`
5. `src/data_clean/service/mcap_io.py`
6. `src/data_clean/config/mcap_process_config.py`
7. `src/data_clean/service/validator.py`

## 11. TDD 执行要求

执行前必须确认当前分支是 `service-s1`。本 L3 涉及代码行为和测试，必须先读取并使用 `$tdd`。

```text
$tdd
```

## 12. 允许修改

- `src/data_clean/service/gripper_width.py`
- `src/data_clean/service/mcap_io.py`
- `src/data_clean/config/`
- `src/data_clean/service/validator.py`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 13. 禁止修改

- 禁止修改浏览器标定 UI。
- 禁止修改位姿转换逻辑。
- 禁止把归一化 gripper width 改成物理单位输出。
- 禁止丢弃现有 `GripperWidthAccumulator` 后另写一套并行实现。

## 14. 验收命令

```bash
python3 -m pytest src/data_clean/tests/service -q
python3 -m pytest src/data_clean/tests/contract -q
```

## 15. 成功标准

- [ ] gripper 输出数量等于 image 帧数。
- [ ] 输出值域保持 `[0, 1]`。
- [ ] 部分缺 marker 可插值并进入统计。
- [ ] 全流无 marker 会失败。
- [ ] 现有双 marker、单 marker、插值逻辑均有针对性测试。
- [ ] 执行摘要说明本次是复用/改造现有实现，不是从零实现。

## 16. 完成后交接

必须更新当前 L3 文件、追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/service-s1-g3/`。
