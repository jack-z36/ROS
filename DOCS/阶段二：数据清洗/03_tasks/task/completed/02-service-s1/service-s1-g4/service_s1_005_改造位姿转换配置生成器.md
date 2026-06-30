# L3 微元任务：改造位姿转换配置生成器

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
L2 能力：位姿转换配置生成
L3 编号：service_s1_005
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g4/service_s1_005_改造位姿转换配置生成器.md`
任务类别：流程编排类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/位姿转换配置生成.md`

## 2. 本次目标

```text
复用已有 calibration wizard，采样右手 T_right_start_common 并求逆写入 frame_alignment 配置。
```

## 3. 本次不做

- 不实现 pose 转换写出。
- 不修改夹爪配置生成流程。
- 不实现统一 `--dev` 一级入口。

## 4. 执行对象

- `src/data_clean/ui/mcap_calibration_wizard.py`
- `config/data_clean/data_clean_calibrated.yaml`
- [[FrameAlignmentConfig]]
- [[Scene1DevRun]]

## 5. 执行依赖

- service_s1_004 已定义配置加载和字段方向。
- calibration wizard 已有旧 common frame 采样与 transform YAML 写回逻辑。
- 新 L2 算法要求默认 `common_anchor = left`，并通过 `common_from_right_start = inverse(T_right_start_common)` 生成右手 start 到 common frame 外参。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：frame_alignment 配置契约
上游接口定义位置：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g4/service_s1_004_落地frame_alignment配置契约.md
当前 L3 期望消费的字段 / 文件 / 返回值：common_anchor、pose_streams、T_right_start_common、common_from_*_start、camera_from_*_tcp
是否存在接口冲突：旧向导写 start_from_common，且旧描述可能把 common_from_right_start 当成固定底座直接输入
如果有冲突，本次处理策略：新写出以 frame_alignment 为准；采样右手 raw pose 得到 T_right_start_common，对其求逆后写入 common_from_right_start；旧字段只作为兼容或迁移输入
```

## 7. 预期改动形态

- dev 检验项可生成临时 `frame_alignment_config.yaml`。
- 默认 `common_anchor: left`。
- 当右手 Baton Mini 被放到 common frame 标定位姿时，读取该帧 raw pose 作为 `T_right_start_common`。
- 对 `T_right_start_common` 求逆后写入 `common_from_right_start`。
- 输出摘要记录外参来源和是否保存到正式配置。

## 8. 现有程序盘点

- `mcap_calibration_wizard.py` 已订阅 Baton pose，支持 common frame 采样窗口，并写 transform YAML。
- 现有输出围绕 `start_from_common`，不符合新 `common_from_*_start` 契约。
- 现有浏览器标定中心可复用，不应重写。
- 现有采样能力应改造成“右手移动到 common frame 标定位姿后采样 raw pose”，而不是要求用户直接填 `common_from_right_start`。

## 9. 本 L3 的真实改造边界

- 复用 wizard，只改位姿配置生成/写回链路。
- 不新增桌面 origin frame。
- 不改 pose 转换算法。
- 本 L3 负责对 `T_right_start_common` 求逆并生成配置，不负责判断人工放置标定位姿是否足够准确。

## 10. 编排输出

### 调用顺序

```text
dev 菜单选择 scene1_frame_alignment_config
↓
创建 Scene1DevRun 并读取生产配置
↓
提示开发者把右手 Baton Mini 放到 common_frame 标定位姿
↓
读取右手 raw pose 得到 T_right_start_common
↓
计算 common_from_right_start = inverse(T_right_start_common)
↓
写出 frame_alignment_config.yaml 和 summary.json
↓
开发者选择是否保存到正式配置
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| calibration wizard | 选择检验项后 | pose stream、配置、右手标定位姿采样 | 临时 frame_alignment | 写 run log |
| SE(3) 求逆逻辑 | 采样完成后 | `T_right_start_common` | `common_from_right_start` | 写入失败原因 |
| 配置保存逻辑 | 显式保存时 | 临时配置 | 正式配置 | 保留临时配置 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `ready` | run 目录创建 | `logs/run_log.json` | 显示 run 目录 |
| `success` | 配置生成完成 | `logs/run_log.json` | 显示产物 |
| `failed` | pose/写回失败 | `logs/run_log.json` | 显示错误 |

## 11. 开发者验收入口

`./start_data_clean.sh --dev -> 场景一 -> scene1_frame_alignment_config`

测试产物：`artifacts/frame_alignment_config.yaml`、`artifacts/frame_alignment_summary.json`、`logs/run_log.json`。摘要必须记录 `T_right_start_common` 原始采样值和求逆后的 `common_from_right_start`。

## 12. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/位姿转换配置生成.md`
2. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/FrameAlignmentConfig.md`
3. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1DevRun.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g4/service_s1_004_落地frame_alignment配置契约.md`

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

1. `src/data_clean/ui/mcap_calibration_wizard.py`
2. `src/data_clean/config/mcap_process_config.py`

## 13. TDD 执行要求

执行前必须先完成 L3 任务文件身份校验。本 L3 涉及行为变更，必须先读取并使用 `$tdd`。

```text
$tdd
```

## 14. 允许修改

- `src/data_clean/ui/`
- `src/data_clean/config/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止修改 gripper 配置生成。
- 禁止实现 pose 转换输出。
- 禁止继续写出 `start_from_common` 作为首选配置。
- 禁止要求用户直接手填 `common_from_right_start` 作为首选流程。
- 禁止把 SE(3) 求逆简化成平移取负数。

## 16. 验收命令

```bash
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [x] 生成配置默认 `common_anchor: left`。
- [x] 输出包含 `common_from_left_start`、`common_from_right_start`。
- [x] `common_from_right_start` 由 `inverse(T_right_start_common)` 生成，summary 可追溯原始采样。
- [x] 输出包含 `camera_from_left_tcp`、`camera_from_right_tcp`。
- [x] dev 检验项产物和日志契约明确。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并将当前 L3 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/02-service-s1/service-s1-g4/`。移动后如果 active 功能组为空，删除该空目录。不写共享执行记录。

## 19. 执行摘要

### 执行前读取

1. 上游 L3：`service_s1_004_落地frame_alignment配置契约.md`（已确认配置加载与字段方向）
2. L2 能力模块：`位姿转换配置生成.md`
3. L2 数据定义：`FrameAlignmentConfig.md`、`Scene1DevRun.md`
4. 约束文档：L3 编码执行原则、身份校验、TDD 与归档、功能分支接力、L3 功能组目录、上游依赖接口对齐、文件存放规范、L3 现有实现盘点、场景一执行约束

### 修改文件

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `src/data_clean/ui/mcap_calibration_wizard.py` | 修改 | 新增 `_se3_inverse_xyzw`、`CommonFrameRightCalibration`、`_sample_right_common_frame_pose`、`_save_frame_alignment_from_right`、`_apply_frame_alignment_from_right`、`_to_mapping_from_transform`；修改 `_sample_current_common_frame` 区分左右手处理 |
| `src/data_clean/ui/scene1_dev_checks.py` | 新增 | dev 检验项 `scene1_frame_alignment_config` 实现，生成 `frame_alignment_config.yaml`、`frame_alignment_summary.json`、`run_log.json` |
| `src/data_clean/ui/dev_menu.py` | 新增 | `--dev` 交互式菜单入口 |
| `start_data_clean.sh` | 修改 | 新增 `--dev` 参数路由到 `ui.dev_menu` |
| `src/data_clean/tests/service/test_scene1_frame_alignment_config.py` | 新增 | SE(3) 求逆测试（identity、pure translation、double inverse、Z rotation）、dev check 测试（config/summary/run_log 生成、加载校验、override） |

### TDD 执行

- **RED**: 先写 SE(3) 求逆测试和 dev check 测试
- **GREEN**: 实现 `_se3_inverse_xyzw`、`CommonFrameRightCalibration`、`_sample_right_common_frame_pose`、`_save_frame_alignment_from_right`、dev check 函数
- **Refactor**: 发现 `_to_mapping` 和 `_to_mapping_from_transform` 重复，保持分离以兼容旧代码路径
- 验收命令：`python3 -m pytest src/data_clean/tests/service/test_scene1_frame_alignment_config.py src/data_clean/tests/config/test_frame_alignment_config.py -q` → 26 passed

### 对 `./start_data_clean.sh --dev` 的影响

- 新增 `--dev` 参数，进入场景菜单
- 场景一新增功能检验项 `scene1_frame_alignment_config`
- 产物：`artifacts/frame_alignment_config.yaml`、`artifacts/frame_alignment_summary.json`、`logs/run_log.json`
- 实时标定中心（`--calibrate`）右手 common frame 标定时自动使用 `inverse(T_right_start_common)` 生成 `common_from_right_start`

### 明确没做

- 不实现 pose 转换输出（下游 L3 负责）
- 不修改夹爪配置生成流程
- 不实现统一 `--dev` 一级入口的场景完整 smoke test
- 不新增桌面 origin frame
- 不改 pose 转换算法

### 后续建议

- 下一个 L3 应实现 common frame 位姿转换算法，消费 `FrameAlignmentConfig` 并输出 `CommonFrameCameraPose` / `CommonFrameTcpPose`
- 场景最终验收需用户本人运行 `./start_data_clean.sh --dev` 选择场景一和 `scene1_frame_alignment_config` 后确认
