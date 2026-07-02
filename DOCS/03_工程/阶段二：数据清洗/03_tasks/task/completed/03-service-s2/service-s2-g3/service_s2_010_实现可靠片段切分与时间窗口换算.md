# L3 微元任务：实现可靠片段切分与时间窗口换算

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：位姿滤波器
L3 编号：service_s2_010
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_010_实现可靠片段切分与时间窗口换算.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_010
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_010_实现可靠片段切分与时间窗口换算.md
  group: service-s2-g3
  branch: service-s2
  wave: 2
  parallel_group: service-s2-g3-p2
  depends_on: [service_s2_007, service_s2_009]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_011, service_s2_012]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [pose_filter.window_duration_ms, pose_filter.polyorder]
  dispatch_status: ready
```

## 3. 本次目标

```text
实现位姿滤波器的可靠片段切分、时间窗口到奇数样本窗口换算和短片段处理。
```

## 4. 本次不做

- 不实现 Savitzky-Golay 数值滤波。
- 不实现四元数姿态滤波。
- 不接入开发者入口。

## 5. 执行对象

- [[PoseFilterInputSequence]]
- [[PoseFilterConfig]]
- [[PoseFilterSegmentSummary]]

## 6. 执行依赖

- `service_s2_007` 已完成并归档，补全后 pose 序列和 [[SignalRepairResult]] 可用。
- `service_s2_009` 已完成并归档，位姿滤波器类型已落地。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：数据补全器、位姿滤波器类型定义
上游接口定义位置：SignalRepairResult.md、PoseFilterInputSequence.md、PoseFilterConfig.md
当前 L3 期望消费的字段 / 文件 / 返回值：output_sequence_refs 映射后的 pose samples、MissingIntervalIssue、pose unrepaired/skipped refs
是否存在接口冲突：无
如果有冲突，本次处理策略：停止并回报，不自行兼容多个猜测格式
```

## 8. 预期改动形态

- `src/data_clean/service/` 中出现可测试的 pose 分段与窗口换算逻辑。
- 测试覆盖缺失区间、未修复样本、短片段和 200ms 时间窗口换算。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法连续 pose 片段 | 按时间戳中位 `dt` 将 200ms 换算为最近奇数样本窗口 | `PoseFilterSegmentSummary.status=filtered` | 无 |
| 含 [[MissingIntervalIssue]] | 缺失区间两侧切为独立片段 | 多个片段摘要 | `split_by_missing_interval` |
| 含 pose `unrepaired` / `skipped` 样本 | 该样本作为边界，不进入滤波窗口 | 左右片段分别输出 | `split_by_unrepaired_pose` |
| 片段过短 | 缩小到可用最大奇数窗口；仍不满足则原样保留 | `kept_original_short_segment` | `short_segment_kept_original` |
| 时间戳重复或倒退 | 当前片段原样保留 | `skipped_invalid_time` | `invalid_segment_time_order` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `segment_id` | string | 片段 id | 同一次运行内唯一 |
| `actual_window_size_samples` | integer/null | 实际窗口 | 奇数且大于 `polyorder` |
| `median_dt_sec` | number/null | 时间戳中位间隔 | 合法片段必须非负 |
| `status` | enum string | 片段状态 | 与 reason 一致 |

## 10. 数据计算验收重点

- 缺失区间阻断跨段滤波。
- pose `unrepaired` / `skipped` 样本阻断跨段滤波。
- 200ms 窗口按中位 `dt` 换算为奇数样本窗口。
- 短片段自适应缩窗或原样保留。

## 11. 现有程序盘点

- `src/data_clean/service/` 尚未发现位姿滤波器实现。
- 现有 `tcp_transform.py` 只负责场景一位姿变换，不负责可靠性滤波。
- 本 L3 应新增独立 service 逻辑，复用现有分层，不改场景一清洗路径。

## 12. 本 L3 的真实改造边界

- 允许新增位姿分段和窗口换算函数。
- 允许新增对应单元测试。
- 禁止实现数值滤波和 MCAP 写出。
- 禁止修改上游数据补全器输出语义。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/位姿滤波器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterInputSequence.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/PoseFilterSegmentSummary.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/MissingIntervalIssue.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_007_实现三模态补全计算规则.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/service_s2_009_定义位姿滤波器配置输入审计记录和结果类型.md`

### 必读约束文档

1. `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
2. `DOCS/02_约束/阶段二任务体系/L3任务文件身份校验约束.md`
3. `DOCS/02_约束/阶段二任务体系/L3调度元数据约束.md`
4. `DOCS/02_约束/阶段二任务体系/L3执行TDD与归档约束.md`
5. `DOCS/02_约束/阶段二任务体系/功能分支接力流程.md`
6. `DOCS/02_约束/阶段二任务体系/L3功能组目录约束.md`
7. `DOCS/02_约束/阶段二任务体系/开发者验收入口约束.md`
8. `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`
9. `DOCS/02_约束/阶段二任务体系/文件存放规范.md`
10. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/执行约束.md`

### 必读代码

1. `src/data_clean/service/`
2. `src/data_clean/schemas/`
3. `src/data_clean/tests/`

## 14. TDD 执行要求

```bash
bash scripts/init_data_clean_dev.sh
```

必须使用 `$tdd`。

## 15. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_pose_filter` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 是；由入口 L3 接入 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 本 L3 不直接接入开发者入口，但由 `scene2_pose_filter` 间接覆盖 |

## 16. 允许修改

- `src/data_clean/service/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止实现数值滤波。
- 禁止写 MCAP_A。
- 禁止修改开发者入口。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [x] 缺失区间会切断片段。
- [x] pose `unrepaired` / `skipped` 样本会切断片段。
- [x] 200ms 时间窗口按中位 `dt` 换算为奇数样本窗口。
- [x] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/`。

## 21. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_010_实现可靠片段切分与时间窗口换算.md
实际读取路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g3/service_s2_010_实现可靠片段切分与时间窗口换算.md
文件名编号：service_s2_010
正文 L3 编号：service_s2_010
dispatch.task_id：service_s2_010
校验结论：通过
```

### 调度与开工自检

- 调度元数据校验：`task_id`、`task_file`、`group`、`branch`、`depends_on`、`dispatch_status` 均允许执行；当前分支为 `service-s2`。
- 上游依赖：已读取归档任务 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_007_实现三模态补全计算规则.md` 和 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/service_s2_009_定义位姿滤波器配置输入审计记录和结果类型.md`，确认本 L3 消费补全后的 pose 序列语义、缺失区间和 pose `unrepaired` / `skipped` 边界。
- 开工自检：`bash scripts/init_data_clean_dev.sh` 通过，输出 `Data clean dev environment OK`。

### 本次修改文件

- `src/data_clean/service/pose_segment.py`：新增 `split_reliable_segments`、`compute_actual_window`、`handle_short_segment`，实现缺失区间边界、未修复样本边界、时间顺序异常、200ms 窗口换算和短片段处理。
- `src/data_clean/tests/service/test_pose_segment.py`：新增 6 个行为测试，覆盖连续片段、缺失区间、未修复样本、短片段、时间顺序异常和 200ms 窗口换算。
- `src/data_clean/data_clean_architecture.md`：登记新增 `service/pose_segment.py`。
- 当前 L3 任务文件：勾选成功标准并记录执行摘要。

### TDD 过程

- Red：先新增 `test_clean_contiguous_pose_becomes_single_filtered_segment`，运行 `python3 -m pytest src/data_clean/tests/service/test_pose_segment.py -q`，按预期因 `ModuleNotFoundError: No module named 'service.pose_segment'` 失败。
- Green：新增 `src/data_clean/service/pose_segment.py`，实现最小连续片段摘要后扩展垂直切片。
- Incremental：逐步补充并实现缺失区间切分、pose `unrepaired` 边界、短片段保留、时间戳重复/倒退跳过和 200ms 按中位 `dt` 换算为最近奇数样本窗口。
- Refactor：抽取样本引用解析、缺失区间判断、窗口奇数化和摘要构造辅助函数，并补充架构登记。

### 验证结果

- `bash scripts/init_data_clean_dev.sh`：通过。
- `python3 -m pytest src/data_clean/tests/service/test_pose_segment.py -q`：通过，`6 passed`。
- `python3 -m pytest src/data_clean/tests/service/test_pose_segment.py -v`：通过，6 个测试全部 PASSED。
- `python3 -m py_compile src/data_clean/service/pose_segment.py src/data_clean/tests/service/test_pose_segment.py`：通过。
- 手动接口验证：通过 `PYTHONPATH=src/data_clean python3 -c ...` 调用 `split_reliable_segments` 和 `compute_actual_window`，观察到 `/pose:0-6 filtered 5`。
- LSP diagnostics：无法执行，当前环境缺少 `basedpyright-langserver`；Markdown 文件无已配置 LSP。

### 成功标准核对

- 已验证 `MissingIntervalIssue` 会在相邻样本跨缺失区间时切断片段，且不跨段滤波。
- 已验证 pose `unrepaired` / `skipped` 样本引用会作为边界被排除，左右片段分别输出摘要。
- 已验证 200ms 窗口按片段时间戳中位 `dt` 换算为最近奇数样本窗口；50ms 采样间隔换算为 5 个样本。
- 本 L3 不直接修改 `./start_data_clean.sh --dev`；后续由场景二 `scene2_pose_filter` 功能检验项和场景完整 smoke test 间接覆盖。建议用户在场景二位姿滤波链路完成后运行 `./start_data_clean.sh --dev`，选择场景二和 `scene2_pose_filter` 做最终人工验收。

### 本次明确未做

- 未实现 Savitzky-Golay 数值滤波。
- 未实现位置滤波、姿态滤波、guard 审计或 MCAP_A 写出。
- 未修改开发者入口、菜单、脚本调用、调度索引、共享执行记录、阶段进度或总执行日志。

### 归档状态

- 本文件完成后移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g3/`。
- 原 active 功能组目录仍包含 `service_s2_011_实现位置姿态滤波与guard审计.md` 和 `service_s2_012_接入位姿滤波开发者功能检验项.md`，因此未删除。

### 风险与后续建议

- `PoseFilterSegmentSummary` 既有 schema 构造字段少于 L2 文档列出的完整摘要字段；本 L3 未越界修改 schema，而是在返回的 `PoseFilterSegmentSummary` 实例上补齐 `segment_id`、`sample_count`、`median_dt_sec`、`status`、`reason` 等本 L3 要求的可观察摘要属性。建议后续 Win 端或专门 schema L3 同步字段定义。
- 建议后续 `service_s2_011` 复用本 L3 的片段摘要和实际窗口，不跨缺失区间或未修复边界执行数值滤波。
