# L3 微元任务：定义 IK 与 MCAP_B 数据契约

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：IK 求解与 MCAP_B 生成器
L3 编号：service_s2_022
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g6/service_s2_022_定义IK与MCAP_B数据契约.md`
任务类别：数据定义类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_022
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g6/service_s2_022_定义IK与MCAP_B数据契约.md
  group: service-s2-g6
  branch: service-s2
  wave: 1
  parallel_group: service-s2-g6-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_023, service_s2_024, service_s2_025]
  conflict_scope:
    files: [src/data_clean/schemas/, src/data_clean/tests/, DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/]
    modules: [data_clean.schemas]
    config_keys: [scene2.ik_mcap_b]
  dispatch_status: ready
```

## 3. 本次目标

```text
把第 6 模块需要的 common->base、RM65 IK、MCAP_B 和 sidecar 契约落成可导入的代码类型 / schema，并与 L2 原子数据定义对齐。
```

## 4. 本次不做

- 不实现坐标转换计算。
- 不调用睿尔曼 SDK。
- 不写 MCAP_B 文件。

## 5. 执行对象

- [[CommonToRobotBaseTransform]]
- [[RobotBaseTcpPose]]
- [[Rm65IkConfig]]
- [[Rm65IkSampleResult]]
- [[McapB]]
- [[IkSolveSummary]]

## 6. 执行依赖

- 来源 L2 已创建。
- 场景二 L2 数据定义已包含上述原子文档。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：MCAP_A 生成器、场景一 common frame 位姿转换。
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/CommonFrameTcpPose.md
当前 L3 期望消费的字段 / 文件 / 返回值：MCAP_A 中左右 TCP pose 的 topic、timestamp、x/y/z、qx/qy/qz/qw。
是否存在接口冲突：无已知冲突。
如果有冲突，本次处理策略：不改上游，先在类型中显式保留 source ref 和未知问题。
```

## 8. 预期改动形态

- `src/data_clean/schemas/` 中新增或扩展 IK / MCAP_B 相关类型。
- 测试覆盖实例化、序列化、非法值拒绝和左右臂字段。
- L2 数据定义如需补充字段，保持 wikilink 与 L2 一致。

## 9. 数据定义输出

### 需要定义的对象

| 对象 | 类型 | 放置位置 | 下游使用者 |
|---|---|---|---|
| `CommonToRobotBaseTransform` | dataclass / schema | `src/data_clean/schemas/` | common->base 转换 |
| `RobotBaseTcpPose` | dataclass | `src/data_clean/schemas/` | RM65 IK 适配器 |
| `Rm65IkConfig` | dataclass / config schema | `src/data_clean/schemas/` | IK 适配器 |
| `Rm65IkSampleResult` | dataclass / enum | `src/data_clean/schemas/` | MCAP_B 写出器 |
| `McapBWriteConfig` | dataclass | `src/data_clean/schemas/` | MCAP_B 写出器 |
| `IkSolveSummary` | dataclass / JSON schema | `src/data_clean/schemas/` | 报告生成器 |

### 字段或取值

字段以 L2 数据定义文档为准，必须至少覆盖：

- `arm_side=left/right`
- `seed_policy=previous_success`
- `status=success/failed/invalid_input/sdk_error`
- `left_robot_base_from_common` / `right_robot_base_from_common`
- `input_mcap_a` / `output_mcap_b`
- `failure_intervals`

## 10. 数据定义验收重点

- 所有类型能被 `python3` 导入。
- 合法样例能序列化为 JSON。
- 非法四元数、关节角长度不为 6、未知 `arm_side` 能被拒绝或明确报错。
- L2 文档中的每个数据概念都有对应原子文档。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/CommonToRobotBaseTransform.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/IkSolveSummary.md`

### 必读相关微元任务记录

1. 如果存在，读取 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g5/service_s2_017_定义MCAP_A写出配置摘要和契约.md`

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

1. `src/data_clean/schemas/`

## 12. TDD 执行要求

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码新增，必须使用 `$tdd`。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_ik_mcap_b_writer` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 否 |
| 是否允许临时覆盖配置 | 否 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 由后续 `scene2_ik_mcap_b_writer` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/schemas/`
- `src/data_clean/tests/`
- 当前 L3 文件自身

## 15. 禁止修改

- 不实现 IK SDK 调用。
- 不修改 MCAP_A 生成器。
- 不修改开发者入口。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "ik_contract or mcap_b_contract"
python3 - <<'PY'
from data_clean.schemas import *
print("ik schema import ok")
PY
```

## 17. 成功标准

- [ ] IK / MCAP_B 类型可导入。
- [ ] 合法样例可实例化并序列化。
- [ ] 非法枚举、关节角长度和四元数输入有明确失败。
- [ ] 原子数据定义与代码字段无明显冲突。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

完成后归档到：

```text
DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/
```

