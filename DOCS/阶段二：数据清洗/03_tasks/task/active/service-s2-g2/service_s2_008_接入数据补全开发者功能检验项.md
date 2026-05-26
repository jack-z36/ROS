# L3 微元任务：接入数据补全开发者功能检验项

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：数据补全器
L3 编号：service_s2_008
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_008_接入数据补全开发者功能检验项.md`
任务类别：流程编排类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_008
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g2/service_s2_008_接入数据补全开发者功能检验项.md
  group: service-s2-g2
  branch: service-s2
  wave: 4
  parallel_group: service-s2-g2-p4
  depends_on: [service_s2_004, service_s2_007]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files: [start_data_clean.sh, src/data_clean/runtime/, src/data_clean/ui/, src/data_clean/tests/]
    modules: [data_clean.runtime, data_clean.ui]
    config_keys: [dev_menu.scene2.signal_repair]
  dispatch_status: ready
```

## 3. 本次目标

```text
把数据补全器接入 ./start_data_clean.sh --dev 的场景二功能检验项 scene2_signal_repair。
```

## 4. 本次不做

- 不新增补全算法。
- 不写 MCAP_A。
- 不接入位姿/触觉滤波器。

## 5. 执行对象

- 场景二开发者菜单。
- 补全器调用顺序。
- `signal_repair_result.json` 调试产物。
- 修复后序列 artifact。
- 运行日志。

## 6. 执行依赖

- `service_s2_004` 已完成并归档，异常检测开发者入口可产出 detection result。
- `service_s2_007` 已完成并归档，补全计算可产出 repair result。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：异常检测开发者入口、数据补全计算规则
上游接口定义位置：service_s2_004、service_s2_007 完成记录与源码
当前 L3 期望消费的字段 / 文件 / 返回值：cleaned MCAP、signal_reliability_detection_result.json、SignalRepairResult
是否存在接口冲突：未知，执行时必须核对 artifact 字段
如果有冲突，本次处理策略：优先调整入口适配当前已归档接口，不改检测/补全算法语义
```

## 8. 预期改动形态

- `./start_data_clean.sh --dev` 可选择场景二数据补全功能检验项。
- 独立 run 目录写出 `signal_repair_result.json`、修复后序列 artifact 和运行日志。

## 9. 编排输出

```text
./start_data_clean.sh --dev
↓
选择场景二
↓
选择 scene2_signal_repair
↓
选择 cleaned MCAP、signal_reliability_detection_result.json 和临时补全策略
↓
运行数据补全器
↓
写 signal_repair_result.json、repaired_sequences 和运行日志
```

## 10. 流程编排验收重点

- 调用顺序正确。
- 不写正式生产输出。
- 能展示 repaired/unrepaired/skipped 统计。
- 运行日志能定位输入、策略、输出和错误。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/数据补全器.md`
2. `DOCS/阶段二：数据清洗/约束文件/开发者验收入口约束.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g1/service_s2_004_接入异常检测开发者功能检验项.md`
2. `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/service_s2_007_实现三模态补全计算规则.md`

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
| 对应功能检验项 | `scene2_signal_repair` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是 |
| 是否需要写测试产物 | 是；`signal_repair_result.json`、`repaired_sequences/`、可选 tactile diff |
| 是否需要写运行日志 | 是；最低字段：输入、检测结果、策略、统计、错误、输出位置 |
| 是否允许临时覆盖配置 | 是 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 用户运行 `./start_data_clean.sh --dev` 选择场景二和 `scene2_signal_repair` |

## 14. 允许修改

- `start_data_clean.sh`
- `src/data_clean/runtime/`
- `src/data_clean/ui/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 15. 禁止修改

- 禁止写正式生产输出。
- 禁止实现滤波器或 MCAP_A 生成器。
- 禁止移动其他 L3。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests -q
```

## 17. 成功标准

- [ ] 场景二 dev 菜单包含 `scene2_signal_repair`。
- [ ] 功能检验项能读取检测结果 artifact。
- [ ] 功能检验项能写出 repair result 和修复后序列 artifact。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 18. 完成后交接

完成后归档到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g2/`。

