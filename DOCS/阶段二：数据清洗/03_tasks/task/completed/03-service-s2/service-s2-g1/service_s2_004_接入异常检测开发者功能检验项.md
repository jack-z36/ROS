# L3 微元任务：接入异常检测开发者功能检验项

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：异常值检测器
L3 编号：service_s2_004
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_004_接入异常检测开发者功能检验项.md`
任务类别：流程编排类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/异常值检测器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_004
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_004_接入异常检测开发者功能检验项.md
  group: service-s2-g1
  branch: service-s2
  wave: 3
  parallel_group: service-s2-g1-p3
  depends_on: [service_s2_002, service_s2_003]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_008]
  conflict_scope:
    files: [start_data_clean.sh, src/data_clean/runtime/, src/data_clean/ui/, src/data_clean/tests/]
    modules: [data_clean.runtime, data_clean.ui]
    config_keys: [dev_menu.scene2.signal_reliability_detect]
  dispatch_status: ready
```

## 3. 本次目标

```text
把异常检测能力接入 ./start_data_clean.sh --dev 的场景二功能检验项 scene2_signal_reliability_detect。
```

## 4. 本次不做

- 不新增检测规则。
- 不实现数据补全器。
- 不写正式生产输出。

## 5. 执行对象

- 场景二开发者菜单。
- 异常检测调用顺序。
- `signal_reliability_detection_result.json` 调试产物。
- 运行日志。

## 6. 执行依赖

- `service_s2_002` 与 `service_s2_003` 已完成并归档。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：位姿/夹爪/触觉异常检测规则
上游接口定义位置：service_s2_002、service_s2_003 完成记录与源码
当前 L3 期望消费的字段 / 文件 / 返回值：SignalReliabilityDetectionResult
是否存在接口冲突：未知，执行时必须核对类型与 L2 字段
如果有冲突，本次处理策略：优先调整入口适配当前已归档接口，不改检测规则语义
```

## 8. 预期改动形态

- `./start_data_clean.sh --dev` 可选择场景二异常检测功能检验项。
- 独立 run 目录写出检测结果 JSON 和运行日志。

## 9. 编排输出

```text
./start_data_clean.sh --dev
↓
选择场景二
↓
选择 scene2_signal_reliability_detect
↓
选择 cleaned MCAP 小样本和临时规则配置
↓
运行异常检测
↓
写 signal_reliability_detection_result.json 与运行日志
```

## 10. 流程编排验收重点

- 调用顺序正确。
- 失败时不写正式生产输出。
- 运行日志能反映输入、配置、统计、错误和输出位置。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/异常值检测器.md`
2. `DOCS/阶段二：数据清洗/约束文件/开发者验收入口约束.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/service_s2_002_实现位姿和夹爪样本级异常检测规则骨架.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/service_s2_003_实现触觉样本级异常检测规则骨架.md`

### 必读约束文档

1. `DOCS/阶段二：数据清洗/约束文件/L3编码执行原则.md`
2. `DOCS/阶段二：数据清洗/约束文件/L3任务文件身份校验约束.md`
3. `DOCS/阶段二：数据清洗/约束文件/L3调度元数据约束.md`
4. `DOCS/阶段二：数据清洗/约束文件/L3执行TDD与归档约束.md`
5. `DOCS/阶段二：数据清洗/约束文件/功能分支接力流程.md`
6. `DOCS/阶段二：数据清洗/约束文件/L3功能组目录约束.md`
7. `DOCS/阶段二：数据清洗/约束文件/开发者验收入口约束.md`
8. `DOCS/阶段二：数据清洗/约束文件/上游依赖接口对齐约束.md`
9. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`
10. `DOCS/阶段二：数据清洗/02_service/场景二/执行约束.md`

### 必读代码

1. `start_data_clean.sh`
2. `src/data_clean/runtime/`
3. `src/data_clean/ui/`
4. `src/data_clean/service/`

## 12. TDD 执行要求

```bash
bash scripts/init_data_clean_dev.sh
```

必须使用 `$tdd`。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_signal_reliability_detect` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是 |
| 是否需要写测试产物 | 是；`signal_reliability_detection_result.json` |
| 是否需要写运行日志 | 是；最低字段：输入、配置、执行步骤、统计、错误、输出位置 |
| 是否允许临时覆盖配置 | 是 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 用户运行 `./start_data_clean.sh --dev` 选择场景二和 `scene2_signal_reliability_detect` |

## 14. 允许修改

- `start_data_clean.sh`
- `src/data_clean/runtime/`
- `src/data_clean/ui/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止写正式生产输出。
- 禁止实现数据补全器。
- 禁止移动其他 L3。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [x] 场景二 dev 菜单包含 `scene2_signal_reliability_detect`。
- [x] 功能检验项能写出检测结果 JSON。
- [x] 运行日志包含输入、配置、统计和输出位置。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/`。

## 19. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_004_接入异常检测开发者功能检验项.md
实际读取路径：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/service_s2_004_接入异常检测开发者功能检验项.md
文件名编号：service_s2_004
正文 L3 编号：service_s2_004
dispatch.task_id：service_s2_004
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`dispatch_status` 均允许执行；当前分支为 `service-s2`；依赖 `service_s2_002`、`service_s2_003` 已在 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/` 归档。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。
- 已读取上游 L3：`service_s2_002`、`service_s2_003`；已读取 L2 能力模块、开发者验收入口约束、TDD/归档/调度/写入边界等约束。

### 本次修改文件

- `start_data_clean.sh`：新增 `--dev` 分支，进入 `ui.dev_menu` 开发者引导界面，并在未传 `--config` 时注入默认数据清洗配置。
- `src/data_clean/ui/dev_menu.py`：新增阶段二开发者菜单源码，保留场景一 `SCENE1_CHECKS` 公开契约，新增场景二菜单项 `scene2_signal_reliability_detect`。
- `src/data_clean/runtime/scene2_signal_reliability.py`：新增场景二异常检测编排，读取 cleaned MCAP 样本，依次调用位姿、夹爪、触觉 detector，写 `outputs/signal_reliability_detection_result.json` 与 `run_log.json`。
- `src/data_clean/tests/runtime/test_scene2_signal_reliability_runtime.py`：新增场景二编排测试，覆盖检测结果 JSON、运行日志字段和菜单项注册。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增 `src/data_clean/tests/runtime/test_scene2_signal_reliability_runtime.py`，运行 `python3 -m pytest src/data_clean/tests/runtime/test_scene2_signal_reliability_runtime.py -q`，按预期因 `ModuleNotFoundError: No module named 'runtime.scene2_signal_reliability'` 失败。
- Green：新增 `runtime.scene2_signal_reliability` 与 `ui.dev_menu`，实现 `scene2_signal_reliability_detect` 到 detector 的最小可观察链路，目标测试通过。
- Refactor：补齐 `start_data_clean.sh --dev` 入口、run 目录输出、dataclass/Enum JSON 转换、pose input/output topic 兼容读取和结构化 run log 字段。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/runtime/test_scene2_signal_reliability_runtime.py -q`：通过，`2 passed`。
- `python3 -m pytest src/data_clean/tests/runtime/test_scene2_signal_reliability_runtime.py src/data_clean/tests/service/test_scene1_dev_menu.py -q`：通过，`3 passed`。
- `python3 -m py_compile src/data_clean/runtime/scene2_signal_reliability.py src/data_clean/ui/dev_menu.py src/data_clean/tests/runtime/test_scene2_signal_reliability_runtime.py`：通过。
- `bash -n start_data_clean.sh`：通过。
- `printf 'q\n' | ./start_data_clean.sh --dev`：通过，实际展示开发者引导界面，包含场景二入口。
- `python3 -m pytest src/data_clean/tests -q`：未通过；收集阶段因既有 `src/data_clean/tests/config_tests/test_frame_alignment_config.py` 导入 `repo.config.mcap_process_config.ExtrinsicConfig` 失败中断，该类型不在本 L3 修改范围内。
- LSP diagnostics：当前环境缺少 `basedpyright-langserver`，无法提供 Python LSP 诊断；已用 `py_compile`、目标 pytest 和 shell 语法检查替代。

### 手动接口验证

- 通过 `PYTHONPATH=src/data_clean:src/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap:src/VTLA_octopus-master/octopus/3rdparty/mcap/python/mcap-ros2-support python3` 驱动脚本直接调用 `run_scene2_signal_reliability_detection()`，确认会创建 `src/data_clean/runs/<run_id>/run_log.json` 并记录输入、配置、步骤、统计、错误和输出路径。
- 使用真实历史 MCAP 做手动试跑时，当前 Python 环境读取该文件失败于 `UnsupportedCompressionError: unsupported compression type zstandard`；该环境依赖问题不影响合成样本自动化验收，但建议最终人工验收前确认 MCAP zstandard 支持可用。

### 成功标准核对

- 已验证场景二 dev 菜单包含 `scene2_signal_reliability_detect`。
- 已验证功能检验项编排能写出 `signal_reliability_detection_result.json`。
- 已验证 `run_log.json` 包含输入、配置、执行步骤、统计、错误列表和输出位置。
- 本 L3 直接影响 `./start_data_clean.sh --dev` 的场景二菜单与 `scene2_signal_reliability_detect` 功能检验项；建议用户后续运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_signal_reliability_detect` 做最终人工验收。

### 本次明确未做

- 未新增检测规则。
- 未实现数据补全、数据修复或正式生产输出。
- 未修改共享执行记录、阶段进度、总执行日志或调度索引。

### 归档状态

- 当前 L3 已从 `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g1/` 移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/`。
- 原 active 功能组目录已为空并删除。
