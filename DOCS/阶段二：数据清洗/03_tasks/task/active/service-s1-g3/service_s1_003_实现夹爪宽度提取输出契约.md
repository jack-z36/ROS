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

- [ ] gripper 输出数量等于 image 帧数。
- [ ] 输出值域保持 `[0, 1]`。
- [ ] 部分缺 marker 可插值并进入统计。
- [ ] 全流无 marker 会失败。
- [ ] dev 检验项产物和日志契约明确。

## 19. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并将当前 L3 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/02-service-s1/service-s1-g3/`。移动后如果 active 功能组为空，删除该空目录。不写共享执行记录。
