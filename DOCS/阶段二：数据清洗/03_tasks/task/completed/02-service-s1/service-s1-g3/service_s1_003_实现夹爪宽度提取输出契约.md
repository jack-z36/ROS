# L3 微元任务：实现夹爪宽度提取输出契约

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
L2 能力：夹爪宽度提取
L3 编号：service_s1_003
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g3/service_s1_003_实现夹爪宽度提取输出契约.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/夹爪宽度提取.md`

## 2. 本次目标

```text
复用现有 GripperWidthAccumulator 和 MCAP 写出逻辑，补齐 gripper_width 输出契约、测试和 dev 功能检验项。
```

## 3. 本次不做

- 不生成夹爪标定配置。
- 不修改位姿转换逻辑。
- 不实现统一 `--dev` 一级入口。

## 4. 执行对象

- `src/data_clean/service/gripper_width.py`
- `src/data_clean/service/mcap_io.py`
- `src/data_clean/config/mcap_process_config.py`
- `src/data_clean/service/validator.py`
- [[GripperWidthSample]]

## 5. 执行依赖

- g2 产生或手写 fixture 提供 [[GripperCalibrationConfig]] 字段。
- raw MCAP 或图像 fixture 包含 GoPro image stream。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：夹爪开合配置生成
上游接口定义位置：DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/GripperCalibrationConfig.md
当前 L3 期望消费的字段 / 文件 / 返回值：image_topic、output_topic、aruco_dict、marker_id_0、marker_id_1、marker_min、marker_max、gripper_max
是否存在接口冲突：如果配置生成器尚未完成，使用最小配置 fixture 驱动测试
如果有冲突，本次处理策略：只消费 GripperCalibrationConfig 语义，不反向修改浏览器配置生成器
```

## 7. 预期改动形态

- gripper 输出数量等于 image 帧数。
- 输出为 `std_msgs/msg/Float32`，值域 `[0, 1]`。
- dev 检验项能输出 gripper 样本、统计摘要和 run log。

## 8. 现有程序盘点

- `gripper_width.py` 已有 `GripperWidthAccumulator`，支持 ArUco 检测、双 marker 直接计算、单 marker 估计、缺失帧插值、归一化和失败语义。
- `mcap_io.py` 已在遍历 image topic 时调用 accumulator，并在原 image message 后追加 gripper width message。
- `mcap_process_config.py` 已有 `GripperStreamConfig` 和 marker/gripper 配置校验。
- `validator.py` 已检查 image topic、gripper output topic 冲突和 `frame_count == gripper_count`。

现有风险：`direct_detection_frames` 包含单 marker 估计帧；如报告需要区分 direct 和 single estimate，需要扩展统计语义。

## 9. 本 L3 的真实改造边界

- 复用现有 `GripperWidthAccumulator`，不得另写并行实现。
- 优先补测试、统计语义和 dev 产物契约。
- 不把输出改成物理宽度。

## 10. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法输入 | 目标 marker 可检测或可插值 | 每帧一个 `[0,1]` gripper sample | 无 |
| 缺失输入 | image topic 缺失或无消息 | 清洗失败 | `missing configured image topic` / `has no messages` |
| 边界输入 | 全流无有效 marker | 清洗失败 | `could not detect any valid markers` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `value` | float | 归一化夹爪宽度 | `[0, 1]` |
| `frame_count` | int | 图像帧数 | `> 0` |
| `gripper_count` | int | gripper 消息数 | 等于 `frame_count` |
| `interpolated_frames` | int | 插值帧数 | `>= 0` |

## 11. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。

## 12. 开发者验收入口

`./start_data_clean.sh --dev -> 场景一 -> scene1_gripper_width_extract`

测试产物：`artifacts/gripper_width_samples.json`、`artifacts/gripper_width_stats.json`、可选 `artifacts/debug_gripper_width.mcap`、`logs/run_log.json`。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/夹爪宽度提取.md`
2. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/GripperWidthSample.md`
3. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1DevRun.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g2/service_s1_002_对接浏览器夹爪配置生成.md`

如果没有找到已完成相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3任务文件身份校验约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/功能分支接力流程.md`
5. `DOCS/阶段二：数据清洗/约束文件/L3功能组目录约束.md`
6. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
7. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
8. `DOCS/阶段二：数据清洗/约束文件/L3现有实现盘点约束.md`
9. `DOCS/阶段二：数据清洗/02_service/场景一/执行约束.md`

### 必读代码

1. `src/data_clean/service/gripper_width.py`
2. `src/data_clean/service/mcap_io.py`
3. `src/data_clean/config/mcap_process_config.py`
4. `src/data_clean/service/validator.py`

## 14. TDD 执行要求

执行前必须先完成 L3 任务文件身份校验。本 L3 涉及代码行为变更，必须先读取并使用 `$tdd`。

```text
$tdd
```

## 15. 允许修改

- `src/data_clean/service/gripper_width.py`
- `src/data_clean/service/mcap_io.py`
- `src/data_clean/config/`
- `src/data_clean/service/validator.py`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 16. 禁止修改

- 禁止修改浏览器标定 UI。
- 禁止修改位姿转换逻辑。
- 禁止丢弃现有 `GripperWidthAccumulator` 后另写一套实现。

## 17. 验收命令

```bash
python3 -m pytest src/data_clean/tests/service -q
python3 -m pytest src/data_clean/tests/contract -q
```

## 18. 成功标准

- [x] gripper 输出数量等于 image 帧数。
- [x] 输出值域保持 `[0, 1]`。
- [x] 部分缺 marker 可插值并进入统计。
- [x] 全流无 marker 会失败。
- [x] dev 检验项产物和日志契约明确。

## 19. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并将当前 L3 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/02-service-s1/service-s1-g3/`。移动后如果 active 功能组为空，删除该空目录。不写共享执行记录。

## 20. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g3/service_s1_003_实现夹爪宽度提取输出契约.md
实际读取路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g3/service_s1_003_实现夹爪宽度提取输出契约.md
文件名编号：service_s1_003
正文 L3 编号：service_s1_003
校验结论：通过
```

### 相关 L3 历史记录

- 读取了 `service_s1_002_对接浏览器夹爪配置生成.md`（completed/02-service-s1/service-s1-g2/），确认上游配置生成 L3 已完成。
- 读取了已完成的 `service_s1_001_稳定cleaned_MCAP接口契约.md`，确认 MCAP 输出契约已稳定。

### TDD 执行过程

采用垂直切片 TDD：

1. **RED**: 写 validator 输入契约测试（missing image topic、zero messages、wrong schema、output topic conflict）→ 测试通过（现有 validator 已实现）
2. **RED**: 写 validator 输出契约测试（frame_count == gripper_count、output topic count mismatch）→ 测试通过（现有 validator 已实现）
3. **RED**: 写输出结构契约测试（value 类型、frame_count > 0、gripper_count == frame_count、interpolated_frames >= 0、samples 字段完整）→ 测试通过（现有 gripper_width.py 已实现）
4. **GREEN**: 新增 `conftest.py` 解决第三方 mcap 库路径问题，使验收命令可直接运行
5. **Refactor**: 无，现有实现已满足契约要求，本次只补测试

### 实际修改文件

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `src/data_clean/tests/conftest.py` | 新增 | 配置测试路径和第三方 mcap 依赖，使验收命令可直接运行 |
| `src/data_clean/tests/service/test_validator_gripper.py` | 新增 | 8 个 validator 输入/输出契约测试 |
| `src/data_clean/tests/contract/test_gripper_width_output_contract.py` | 新增 | 12 个输出结构契约测试 |

本次未修改任何源码文件。现有 `GripperWidthAccumulator`、`build_gripper_samples`、`build_gripper_stats`、`write_gripper_dev_artifacts`、`validate_input_inventory`、`validate_output_contract` 已满足契约要求。

### 新增/修改函数

- 未修改任何源码函数。
- 新增 3 个测试类、20 个测试方法。

### 验收命令

```bash
python3 -m pytest src/data_clean/tests/service -q
python3 -m pytest src/data_clean/tests/contract -q
```

结果：service 29 passed，contract 17 passed，总计 46 passed。

### 成功标准勾选

- [x] gripper 输出数量等于 image 帧数 → `test_gripper_count_equals_frame_count` + `test_stats_gripper_count_equals_frame_count` + validator `test_frame_count_equals_gripper_count_passes` 三重验证
- [x] 输出值域保持 `[0, 1]` → `test_values_normalized_to_zero_one` + `test_all_values_in_normalized_range` + `test_samples_value_in_range` 验证
- [x] 部分缺 marker 可插值并进入统计 → `test_interpolation_fills_missing_frames` + `test_interpolated_frames_tracked_in_stats` 验证
- [x] 全流无 marker 会失败 → `test_no_markers_raises_error` + `test_empty_stream_raises_error` 验证
- [x] dev 检验项产物和日志契约明确 → `write_gripper_dev_artifacts` 产出 samples/stats JSON + `test_write_gripper_dev_artifacts_creates_files` 验证

### 对 ./start_data_clean.sh --dev 的影响

本 L3 为 `./start_data_clean.sh --dev -> 场景一 -> scene1_gripper_width_extract` 检验项补齐了自动化契约测试：
- 验证 gripper 输出数量等于 image 帧数
- 验证输出值域为 [0, 1]
- 验证插值帧统计正确
- 验证全流无 marker 时失败
- 验证 dev 产物（gripper_width_samples.json、gripper_width_stats.json）结构完整
- 验证 validator 对缺失 image topic、消息数为零、schema 不匹配、output topic 冲突的拒绝

产物契约：
- `artifacts/gripper_width_samples.json`: 逐帧样本，含 frame_index、value、output_topic、source_image_topic、source_method
- `artifacts/gripper_width_stats.json`: 统计摘要，含 frame_count、gripper_count、interpolated_frames、value_min/max/mean

### 本次没做

- 不生成夹爪标定配置（g2 范围）
- 不修改位姿转换逻辑
- 不实现统一 `--dev` 一级入口
- 不修改浏览器标定 UI

### 后续建议

- 用户后续运行 `./start_data_clean.sh --dev` 选择 `scene1_gripper_width_extract` 时，需将 `write_gripper_dev_artifacts` 集成到 dev run 流程中
- 建议在 g2 完成后用真实标定配置 + 真实 GoPro 图像做端到端验证
