# L3 微元任务：对接浏览器夹爪配置生成

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
L2 能力：夹爪开合配置生成
L3 编号：service_s1_002
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g2/service_s1_002_对接浏览器夹爪配置生成.md`
任务类别：流程编排类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/夹爪开合配置生成.md`

## 2. 本次目标

```text
复用已有 calibration wizard，把夹爪配置生成接入场景一 dev 功能检验项 scene1_gripper_calibration_config。
```

## 3. 本次不做

- 不实现夹爪宽度提取算法。
- 不修改 common frame 位姿转换。
- 不实现统一 `--dev` 一级入口。

## 4. 执行对象

- `src/data_clean/ui/mcap_calibration_wizard.py`
- `config/data_clean/data_clean_calibrated.yaml`
- [[GripperCalibrationConfig]]
- [[Scene1DevCheckItem]]

## 5. 执行依赖

- g1 dev 数据定义已存在。
- 现有浏览器标定程序可启动 HTTP 服务、显示 GoPro 图像并写回 YAML。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：GoPro live image 与现有浏览器标定向导
上游接口定义位置：src/data_clean/ui/mcap_calibration_wizard.py；DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/GripperCalibrationConfig.md
当前 L3 期望消费的字段 / 文件 / 返回值：image_topic、output_topic、marker_id_0、marker_id_1、marker_min、marker_max、gripper_max
是否存在接口冲突：用户描述包含点击两个点，现有程序可能主要是 ArUco 采样
如果有冲突，本次处理策略：优先复用已有采样和 YAML 写回；缺点击点位时只补最小点位采集，不重写 UI
```

## 7. 预期改动形态

- `scene1_gripper_calibration_config` 检验项可被未来 dev 菜单调用。
- 生成临时 gripper 配置、摘要和 run log。
- 默认不写回生产配置；显式保存才写回。

## 8. 现有程序盘点

- `mcap_calibration_wizard.py` 已包含浏览器页面、HTTP server、GoPro 图像订阅、终端兜底流程和 YAML 写回。
- 已有 gripper 标定流程会写 `gripper_streams` 与 `calibration.gripper`。
- 现有风险是网页交互是否满足“点击两个点”描述，需要执行端先确认。

## 9. 本 L3 的真实改造边界

- 复用现有 calibration wizard，不新增第二套标定中心。
- 只把输出字段、dev 检验项、产物和日志收敛到 [[GripperCalibrationConfig]] / [[Scene1DevRun]] 契约。
- 不改 gripper width 计算。

## 10. 编排输出

### 调用顺序

```text
dev 菜单选择 scene1_gripper_calibration_config
↓
读取生产配置并创建 Scene1DevRun
↓
调用现有 calibration wizard 的夹爪配置流程
↓
写出临时 gripper_calibration_config.yaml、summary.json、run_log.json
↓
开发者选择是否保存到正式配置
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| `mcap_calibration_wizard.py` | 进入检验项后 | 生产配置、GoPro 图像 | 临时配置 | 写入 run log 并失败 |
| 配置写回逻辑 | 开发者确认保存时 | 临时配置 | 正式配置 | 失败时保留临时产物 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `ready` | run 目录创建完成 | `logs/run_log.json` | 显示 run 目录 |
| `success` | 左右配置生成完成 | `logs/run_log.json` | 显示产物路径 |
| `failed` | 图像/写回失败 | `logs/run_log.json` | 显示错误原因 |

## 11. 开发者验收入口

`./start_data_clean.sh --dev -> 场景一 -> scene1_gripper_calibration_config`

测试产物：`artifacts/gripper_calibration_config.yaml`、`artifacts/gripper_calibration_summary.json`、`logs/run_log.json`。

## 12. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/夹爪开合配置生成.md`
2. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/GripperCalibrationConfig.md`
3. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1DevRun.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g1/service_s1_001_稳定cleaned_MCAP接口契约.md`

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

- 禁止重写浏览器标定中心。
- 禁止修改夹爪宽度提取算法。
- 禁止实现统一 `--dev` 一级入口。

## 16. 验收命令

```bash
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [x] dev 检验项产物契约明确。
- [x] 配置写回符合 [[GripperCalibrationConfig]]。
- [x] 执行摘要说明现有 wizard 复用情况。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并将当前 L3 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/02-service-s1/service-s1-g2/`。移动后如果 active 功能组为空，删除该空目录。不写共享执行记录。

## 19. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g2/service_s1_002_对接浏览器夹爪配置生成.md
实际读取路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g2/service_s1_002_对接浏览器夹爪配置生成.md
文件名编号：service_s1_002
正文 L3 编号：service_s1_002
校验结论：通过
```

### 本次读取的相关 L3 任务文件或执行记录

- 未找到相关 L3 历史记录（service-s1-g1 的 service_s1_001 路径不存在）。

### TDD red / green / refactor 过程

1. **RED:** 编写 `TestCreateScene1DevRun` 测试 dev run 目录创建和 run_log.json 初始状态 → 测试失败（函数不存在）
2. **GREEN:** 实现 `Scene1DevRun` dataclass 和 `create_scene1_dev_run()` 函数 → 3 tests pass
3. **RED:** 编写 `TestWriteGripperCalibrationArtifacts` 测试临时配置和摘要写入 → 测试失败（函数不存在）
4. **GREEN:** 实现 `write_gripper_calibration_artifacts()` 函数 → 4 tests pass (total 7)
5. **RED:** 编写 `TestSaveGripperCalibrationToProduction` 测试显式保存到生产配置 → 测试失败（函数不存在）
6. **GREEN:** 实现 `save_gripper_calibration_to_production()` 函数 → 2 tests pass (total 9)

### 实际修改的文件

1. `src/data_clean/ui/mcap_calibration_wizard.py` - 新增 `Scene1DevRun`、`create_scene1_dev_run()`、`write_gripper_calibration_artifacts()`、`save_gripper_calibration_to_production()`
2. `src/data_clean/config/__init__.py` - 新建 config 包（修复导入路径问题）
3. `src/data_clean/config/mcap_process_config.py` - 新建 re-export 模块（向后兼容）
4. `src/data_clean/tests/service/test_scene1_gripper_calibration_config.py` - 新建测试文件

### 新增或修改的函数、类

- `Scene1DevRun` (dataclass) - dev run 目录结构定义
- `create_scene1_dev_run(check_id)` - 创建独立 dev run 目录和初始 run_log.json
- `write_gripper_calibration_artifacts(dev_run, results)` - 写出临时 gripper 配置、摘要和更新 run_log
- `save_gripper_calibration_to_production(output_path, results)` - 显式保存夹爪标定到生产配置

### 验收命令

```bash
cd /home/hit/ROS/src/data_clean && PYTHONPATH="" /home/hit/ROS/src/data_clean/.conda-envs/data-clean/bin/python -m pytest tests/service/ -q
```

结果：17 passed（包含 9 个新增测试）

### 对 ./start_data_clean.sh --dev 开发者入口的影响

本 L3 为 `./start_data_clean.sh --dev -> 场景一 -> scene1_gripper_calibration_config` 检验项提供底层函数支持：
- `create_scene1_dev_run()` 创建独立运行目录
- `write_gripper_calibration_artifacts()` 产出 `artifacts/gripper_calibration_config.yaml`、`artifacts/gripper_calibration_summary.json`、`logs/run_log.json`
- `save_gripper_calibration_to_production()` 提供显式保存到生产配置的能力

### 现有 wizard 复用情况

- 完全复用 `mcap_calibration_wizard.py` 中的 `GripperSideCalibration`、`_save_gripper()` 等现有函数
- 未重写浏览器标定中心，未修改夹爪宽度提取算法
- 新增的 dev 检验项函数作为现有 wizard 的上层编排入口

### 明确没做什么

- 未实现统一 `--dev` 一级入口（留给后续 L3）
- 未修改 common frame 位姿转换
- 未实现夹爪宽度提取算法
- 未修改浏览器 UI 交互

### 归档

- 已从 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g2/` 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/02-service-s1/service-s1-g2/`
- 原 active 功能组目录 `service-s1-g2/` 已为空，已删除该空目录
