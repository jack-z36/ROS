# L3 微元任务：接入场景三 aligned MCAP 写出开发者检验项

## 1. 任务定位

阶段：阶段二：数据清洗  
场景：场景三：MCAP 多 topic 时间轴对齐  
L1：service_s3  
L2 能力：aligned MCAP 与 sidecar 写出器  
L3 编号：service_s3_023  
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_023_接入场景三aligned_MCAP写出开发者检验项.md`  
任务类别：流程编排类  
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s3_023
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s3-g6/service_s3_023_接入场景三aligned_MCAP写出开发者检验项.md
  group: service-s3-g6
  branch: service-s3
  wave: 4
  parallel_group: service-s3-g6-p4
  depends_on: [service_s3_022]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files:
      - start_data_clean.sh
      - src/data_clean/runtime/scene3_aligned_mcap_write_check.py
      - src/data_clean/ui/dev_menu.py
      - src/data_clean/tests/
      - src/data_clean/data_clean_architecture.md
    modules:
      - data_clean.runtime
      - data_clean.ui
    config_keys:
      - scene3_alignment.output_dir
  dispatch_status: ready
```

## 3. 本次目标

```text
把 aligned MCAP 与 sidecar 整体写出流程接入场景三开发者检验项 scene3_aligned_mcap_write_check。
```

## 4. 本次不做

- 不新增底层写出算法。
- 不修改 report draft 统计。
- 不修改字段对齐算法。
- 不执行场景最终人工验收。

## 5. 执行对象

- `scene3_aligned_mcap_write_check` 开发者检验项
- aligned MCAP / sidecar / write summary 调试产物
- 运行日志

## 6. 执行依赖

- `service_s3_022` 应已实现临时目录整体提交与失败摘要。
- 必须复用现有开发者入口 / UI 菜单风格。
- 本任务只负责开发者入口编排和可观察产物。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：aligned MCAP 与 sidecar 整体写出服务
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md
- DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcapWriteSummary.md
当前 L3 期望消费的字段 / 文件 / 返回值：
- 完整写出服务输入、输出路径、write summary、失败摘要、运行日志字段
是否存在接口冲突：无已知冲突
如果有冲突，本次处理策略：停止并汇报，不在入口层重写底层写出
```

## 8. 预期改动形态

- 新增或扩展 runtime / UI 开发者检验入口。
- 检验项能选择小样本输入和输出目录，调用整体写出服务。
- 输出 aligned MCAP、`alignment_index.parquet`、`alignment_report.json`、`aligned_mcap_write_summary.json` 和运行日志。

## 9. 编排输出

### 调用顺序

```text
./start_data_clean.sh --dev
↓
选择场景三：MCAP 多 topic 时间轴对齐
↓
选择 scene3_aligned_mcap_write_check
↓
选择小样本输入和调试输出目录
↓
调用 aligned MCAP 与 sidecar 整体写出服务
↓
输出四类测试产物和运行日志
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| aligned MCAP 整体写出服务 | 用户确认输入后 | MCAP_A、FieldAlignmentResult、AlignmentIndex、report draft、配置 | aligned MCAP、sidecar、summary | 写失败摘要和运行日志 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `completed` | 四类产物写出成功 | run log / write summary | 输出路径 |
| `failed` | 任一写出步骤失败 | run log / write summary | 失败原因和诊断路径 |

## 10. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景三/L2能力模块/aligned MCAP 与 sidecar 写出器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景三/L2数据定义/AlignedMcapWriteSummary.md`
3. `DOCS/阶段二：数据清洗/约束文件/开发者验收入口约束.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/service_s3_022_实现临时目录整体提交与失败摘要.md`

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
10. `DOCS/阶段二：数据清洗/02_service/场景三/执行约束.md`

### 必读代码

1. `start_data_clean.sh`
2. `src/data_clean/runtime/`
3. `src/data_clean/ui/`
4. `src/data_clean/tests/`
5. `src/data_clean/data_clean_architecture.md`

## 12. TDD 执行要求

执行前必须完成任务文件身份校验、dispatch 校验和 `service-s3` 分支校验。

执行代码前必须运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及入口编排，必须使用 `$tdd` 技能。建议顺序：runner 调用测试 -> 成功产物路径测试 -> 失败摘要显示测试 -> 菜单接入测试。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景三：MCAP 多 topic 时间轴对齐 |
| 对应功能检验项 | `scene3_aligned_mcap_write_check` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是 |
| 是否需要写测试产物 | 是；产物类型：aligned MCAP、alignment index、alignment report、write summary |
| 是否需要写运行日志 | 是；最低字段：输入、配置、执行步骤、关键状态、错误信息、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` 选择场景三和 `scene3_aligned_mcap_write_check` / 场景完整 smoke test |

## 14. 允许修改

- `start_data_clean.sh`
- `src/data_clean/runtime/`
- `src/data_clean/ui/`
- `src/data_clean/tests/`
- `src/data_clean/data_clean_architecture.md`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止重写底层 sidecar 或 MCAP 写出服务。
- 禁止修改 report draft 统计。
- 禁止修改字段对齐算法。
- 禁止写入共享执行记录。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [ ] 已接入 `scene3_aligned_mcap_write_check`。
- [ ] 检验项能写出 aligned MCAP、alignment index、alignment report 和 write summary。
- [ ] 运行日志包含输入、配置、执行步骤、关键状态、错误信息和输出位置。
- [ ] 失败时能展示失败摘要，不把半成品标记为 completed。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/04-service-s3/service-s3-g6/`。如果 `active/service-s3-g6/` 为空，删除该空目录。不得写共享执行记录。

