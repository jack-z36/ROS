# L3 微元任务：补充 MCAP_A 契约与场景三兼容验收

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：MCAP_A 生成器
L3 编号：service_s2_019
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_019_补充MCAP_A契约与场景三兼容验收.md`
任务类别：数据读写类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_019
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g5/service_s2_019_补充MCAP_A契约与场景三兼容验收.md
  group: service-s2-g5
  branch: service-s2
  wave: 3
  parallel_group: service-s2-g5-p3
  depends_on: [service_s2_018]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files: [src/data_clean/tests/contract/, src/data_clean/tests/]
    modules: [data_clean.tests]
    config_keys: []
  dispatch_status: ready
```

## 3. 本次目标

```text
补充 MCAP_A 契约测试和最小场景三读取兼容验收，证明 MCAP_A 可作为 validated 主 MCAP 被下游读取。
```

## 4. 本次不做

- 不实现或修改场景三时间轴对齐算法。
- 不改变 MCAP_A 写出规则。
- 不接入开发者菜单。

## 5. 执行对象

- [[McapA]]
- [[McapAWriteSummary]]
- 场景三最小读取兼容检查

## 6. 执行依赖

- 执行前 `service_s2_018` 必须已完成并归档，MCAP_A 写出器可生成测试产物。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：MCAP_A 复制替换写出器
上游接口定义位置：MCAP_A生成器 L2、service_s2_018
当前 L3 期望消费的字段 / 文件 / 返回值：MCAP_A 文件、mcap_a_write_summary.json、topic/type/timestamp/sample count
是否存在接口冲突：无
如果有冲突，本次处理策略：以 MCAP_A L2 契约为准，发现写出器不满足则补测试暴露失败，不扩大修改范围
```

## 8. 预期改动形态

- 新增 MCAP_A contract 测试。
- 新增场景三读取兼容的最小 smoke / helper 测试。
- 验证输出路径和 sidecar summary 必填字段。

## 9. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
|---|---|---|---|---|
| 生成或读取测试 MCAP_A | 写出器测试 fixture | 测试输出目录 | MCAP | 测试隔离输出 |
| 读取 summary | `mcap_a_write_summary.json` | 断言字段 | JSON | 只读 |
| 场景三最小读取 | MCAP_A | 可读 topic/time 序列 | MCAP | 只读 |

### 文件或目录结构

```text
src/data_clean/tests/contract/
└── <mcap_a_contract_test>.py

src/data_clean/tests/outputs/
└── <test_run>/
    ├── <stem>_mcap_a.mcap
    └── mcap_a_write_summary.json
```

## 10. 数据读写验收重点

- 测试或命令运行后真实生成预期文件 / 目录。
- 文件内容可解析，必要字段存在。
- 重复运行不会污染旧结果。
- 失败时错误信息清楚，不产生误导性的半成品。

## 11. 现有程序盘点

- 先检查 `src/data_clean/tests/contract/` 是否已有 MCAP / cleaned contract 测试。
- 先检查场景三已有读取入口或 L2 契约；只做最小兼容验证，不提前实现对齐。
- 复用 `service_s2_018` 的写出 fixture 和 helper。

## 12. 本 L3 的真实改造边界

- 允许新增或补充 contract / smoke 测试。
- 允许补充必要测试 fixture 生成逻辑。
- 禁止修改写出器核心逻辑，除非测试暴露小范围契约 bug 且修复不跨模块。
- 禁止实现完整场景三流程。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/McapAWriteSummary.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_018_实现MCAP_A复制替换写出器.md`

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

1. `src/data_clean/tests/contract/`
2. `src/data_clean/tests/`
3. `src/data_clean/repo/`

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
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否，本 L3 补充自动化验收 |
| 是否需要写测试产物 | 是；测试隔离 MCAP_A 和 summary |
| 是否需要写运行日志 | 测试日志即可 |
| 是否允许临时覆盖配置 | 不涉及 |
| 是否允许保存覆盖到配置文件 | 否 |
| 最终人工验收提示 | 本 L3 完成后仍需用户最终运行开发者入口确认 |

## 16. 允许修改

- `src/data_clean/tests/contract/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 17. 禁止修改

- 禁止实现完整场景三时间轴对齐。
- 禁止修改 MCAP_A topic 策略。
- 禁止写真实数据产物到正式生产目录。

## 18. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 19. 成功标准

- [ ] 合同测试验证 MCAP_A 与 cleaned MCAP topic、消息类型、时间戳和样本数对齐。
- [ ] 合同测试验证 sidecar summary 必填字段齐全。
- [ ] 最小场景三读取兼容检查能读取 MCAP_A 的主数据 topic。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 20. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/`。
