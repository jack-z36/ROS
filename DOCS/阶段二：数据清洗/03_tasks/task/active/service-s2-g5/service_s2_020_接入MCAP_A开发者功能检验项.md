# L3 微元任务：接入 MCAP_A 开发者功能检验项

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：MCAP_A 生成器
L3 编号：service_s2_020
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_020_接入MCAP_A开发者功能检验项.md`
任务类别：流程编排类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_020
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_020_接入MCAP_A开发者功能检验项.md
  group: service-s2-g5
  branch: service-s2
  wave: 4
  parallel_group: service-s2-g5-p4
  depends_on: [service_s2_018]
  must_run_after: [service_s2_019]
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files: [start_data_clean.sh, src/data_clean/runtime/, src/data_clean/ui/, src/data_clean/tests/]
    modules: [data_clean.runtime, data_clean.ui]
    config_keys: [dev_menu.scene2.mcap_a_writer]
  dispatch_status: ready
```

## 3. 本次目标

```text
把 MCAP_A 生成器接入 `./start_data_clean.sh --dev` 场景二功能检验项，生成隔离调试产物和运行日志。
```

## 4. 本次不做

- 不修改 MCAP_A 写出器核心逻辑。
- 不接入 IK、MCAP_B、Parquet 标注或场景三完整流程。
- 不默认保存临时覆盖到正式配置。

## 5. 执行对象

- 开发者入口场景二功能检验项 `scene2_mcap_a_writer`
- [[McapA]]
- [[McapAWriteSummary]]

## 6. 执行依赖

- 执行前 `service_s2_018` 必须已完成并归档，MCAP_A 写出器可用。
- 建议 `service_s2_019` 已完成并归档，使入口接入前已有契约测试保障。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：MCAP_A 写出器
上游接口定义位置：MCAP_A生成器 L2、service_s2_018
当前 L3 期望消费的字段 / 文件 / 返回值：cleaned MCAP、signal_repair_result.json、pose_filter_result.json、tactile_filter_result.json、McapAWriteConfig
是否存在接口冲突：无
如果有冲突，本次处理策略：入口只做参数收集、调用和日志；缺少上游 artifact 时清晰失败，不自行生成假数据
```

## 8. 预期改动形态

- 开发者入口中出现或可选择 `scene2_mcap_a_writer` 功能检验项。
- 功能检验运行后写出 `artifacts/mcap_a/<stem>_mcap_a.mcap`、`artifacts/mcap_a_write_summary.json` 和运行日志。
- 临时输出目录和覆盖策略只对本次运行生效。

## 9. 编排输出

### 调用顺序

```text
./start_data_clean.sh --dev
↓
选择场景二：硬件数据可靠性验证
↓
选择 scene2_mcap_a_writer
↓
选择 cleaned MCAP、signal_repair_result.json、pose_filter_result.json、tactile_filter_result.json 和调试输出目录
↓
可选临时覆盖输出目录 / 覆盖策略
↓
执行 MCAP_A 写出器
↓
写出 MCAP_A、mcap_a_write_summary.json 和运行日志
```

### 被调模块

| 被调模块 | 调用时机 | 输入 | 输出 | 失败时处理 |
|---|---|---|---|---|
| 上游结果加载 | 执行前 | 三类 result JSON 或等价 artifact | result refs | 写清缺失项并停止 |
| MCAP_A 写出器 | 输入校验后 | cleaned MCAP、三类 result、[[McapAWriteConfig]] | [[McapA]]、[[McapAWriteSummary]] | 写错误日志并停止 |
| 调试产物写出 | 写出成功后 | [[McapA]]、[[McapAWriteSummary]] | artifacts 和运行日志 | 写出失败原因和已生成文件 |

### 状态记录

| 状态 | 触发条件 | 记录位置 | 用户可见反馈 |
|---|---|---|---|
| `ready` | 输入选择完成 | 运行日志 | 显示输入和配置摘要 |
| `failed` | 输入缺失、校验失败或写出失败 | 运行日志 | 显示 reason 和缺失项 |
| `completed` | MCAP_A 和 summary 写出完成 | 运行日志和终端摘要 | 显示输出目录 |

## 10. 流程编排验收重点

- 调用顺序正确。
- 任一步失败时行为符合 L2 失败策略。
- 状态、日志或错误摘要能反映真实执行结果。
- 不把底层算法细节写进编排层。

## 11. 现有程序盘点

- 先读取 `service_s2_004`、`service_s2_008`、`service_s2_012`、`service_s2_016` 的入口接入方式，保持场景二功能检验菜单风格一致。
- 先检查 `start_data_clean.sh`、`src/data_clean/runtime/`、`src/data_clean/ui/` 中已有开发者入口结构。
- 复用已有 run 目录、运行日志和调试产物写出模式。

## 12. 本 L3 的真实改造边界

- 允许新增 `scene2_mcap_a_writer` 菜单项、runner/CLI glue 和 smoke 测试。
- 允许写开发者调试产物到独立 run 目录。
- 禁止修改 MCAP_A 写出器核心语义。
- 禁止把临时覆盖默认写回正式配置。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteConfig.md`
4. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md`
5. `DOCS/阶段二：数据清洗/约束文件/开发者验收入口约束.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_018_实现MCAP_A复制替换写出器.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_019_补充MCAP_A契约与场景三兼容验收.md`

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
4. `src/data_clean/tests/`

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
| 对应功能检验项 | `scene2_mcap_a_writer` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是 |
| 是否需要写测试产物 | 是；`artifacts/mcap_a/<stem>_mcap_a.mcap`、`artifacts/mcap_a_write_summary.json` |
| 是否需要写运行日志 | 是；最低字段：输入、配置、执行步骤、关键状态、错误信息、输出位置 |
| 是否允许临时覆盖配置 | 是；只对本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` 选择场景二和 `scene2_mcap_a_writer` |

## 16. 允许修改

- `start_data_clean.sh`
- `src/data_clean/runtime/`
- `src/data_clean/ui/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止修改 MCAP_A 写出器核心语义。
- 禁止修改上游补全和滤波结果语义。
- 禁止把开发者调试产物写入正式生产输出目录。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [ ] `scene2_mcap_a_writer` 可从开发者入口触发或被 CLI/smoke 测试覆盖。
- [ ] 功能检验写出 MCAP_A、sidecar summary 和运行日志。
- [ ] 缺少上游 result 时入口清晰失败，不生成误导性 MCAP_A。
- [ ] 临时覆盖配置只对本次运行生效，默认不写回正式配置。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/`。
