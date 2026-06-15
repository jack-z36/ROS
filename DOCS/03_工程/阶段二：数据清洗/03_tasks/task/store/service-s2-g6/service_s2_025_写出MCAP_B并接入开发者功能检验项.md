# L3 微元任务：写出 MCAP_B 并接入开发者功能检验项

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：IK 求解与 MCAP_B 生成器
L3 编号：service_s2_025
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g6/service_s2_025_写出MCAP_B并接入开发者功能检验项.md`
任务类别：数据读写类 / 流程编排类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_025
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g6/service_s2_025_写出MCAP_B并接入开发者功能检验项.md
  group: service-s2-g6
  branch: service-s2
  wave: 4
  parallel_group: service-s2-g6-p4
  depends_on: [service_s2_021, service_s2_022, service_s2_023, service_s2_024]
  must_run_after: []
  can_run_parallel_with: []
  blocks: []
  conflict_scope:
    files: [src/data_clean/repo/, src/data_clean/runtime/, src/data_clean/ui/, start_data_clean.sh, src/data_clean/tests/]
    modules: [data_clean.repo, data_clean.runtime, data_clean.ui]
    config_keys: [dev_menu.scene2.ik_mcap_b_writer]
  dispatch_status: ready
```

## 3. 本次目标

```text
把成功 IK 结果写出为 MCAP_B JointState topic，写出 IkSolveSummary，并接入场景二开发者功能检验项。
```

## 4. 本次不做

- 不重新实现 common->base 转换。
- 不重新实现 IK 求解。
- 不做关节限制、速度、加速度或 MuJoCo 检查。

## 5. 执行对象

- [[McapB]]
- [[IkSolveSummary]]
- `sensor_msgs/msg/JointState`
- 开发者功能检验项 `scene2_ik_mcap_b_writer`

## 6. 执行依赖

- `service_s2_021` 到 `service_s2_024` 全部完成并归档。
- MCAP_A 写出器相关任务完成并归档。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：RM65 SDK IK 求解适配器、MCAP_A 生成器。
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/Rm65IkSampleResult.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapA.md
当前 L3 期望消费的字段 / 文件 / 返回值：逐样本 IK 结果、status、timestamp、joint_deg、arm_side。
是否存在接口冲突：无已知冲突。
如果有冲突，本次处理策略：不伪造关节角，在 sidecar 中记录失败。
```

## 8. 预期改动形态

- repo/service/runtime/ui 中出现 MCAP_B 写出和开发者入口调用链。
- 只写成功 IK 帧到 MCAP_B。
- `IkSolveSummary` 覆盖所有输入 pose。
- `./start_data_clean.sh --dev` 场景二菜单可选择 `scene2_ik_mcap_b_writer`。

## 现有程序盘点

- `src/data_clean/service/mcap_io.py` 已有 MCAP 读取、复制、注册 schema/channel、写消息的样例。
- `src/data_clean/repo/ros2_codec.py` 已有 ROS2 动态消息编码和 `Float32` 编码样例，但尚无 `sensor_msgs/msg/JointState` 编码。
- `start_data_clean.sh` 和 `src/data_clean/runtime/` 已有开发者入口与 runtime 分层基础。
- 本 L3 应复用现有 MCAP writer / ROS2 codec 思路，不得把 MCAP 写出逻辑散落在 UI 层。

## 本 L3 的真实改造边界

- 可以新增 JointState schema 常量、编码函数、MCAP_B 写出器和开发者入口 runner。
- 不允许重写 MCAP_A 写出器。
- 不允许把 IK 计算写进 MCAP_B 写出器。
- 不允许让 UI 直接读写 MCAP。

## 9. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
|---|---|---|---|---|
| 读取 IK 结果 | [[Rm65IkSampleResult]] | 内存写出计划 | dataclass / JSON | 只读 |
| 写 MCAP_B | 成功 IK 样本 | `asset/阶段二：数据清洗/dev/mcap_validated/<stem>_mcap_b.mcap` 或 run artifact | MCAP | 默认不覆盖 |
| 写 IK 摘要 | 全部 IK 样本和写出统计 | `ik_solve_summary.json` | JSON | 同一 run 可覆盖临时产物 |
| 接入开发者入口 | 场景二菜单 | `scene2_ik_mcap_b_writer` | CLI / runtime | 不影响生产默认入口 |

### 文件或目录结构

```text
src/data_clean/runs/<run_id>/
└── outputs/
    └── artifacts/
        └── ik_mcap_b/
            ├── <stem>_mcap_b.mcap
            └── ik_solve_summary.json
```

## 10. 数据读写验收重点

- MCAP_B 能被读取，左右 JointState topic 存在。
- 失败帧不写入 MCAP_B。
- sidecar 覆盖所有输入 pose，包含失败帧。
- 运行日志记录 SDK 来源、输入、配置、统计和输出位置。
- 开发者入口输出在独立 run 目录，不污染正式产物。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/McapB.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/IkSolveSummary.md`
4. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/MCAP_A生成器.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/service_s2_021_建立睿尔曼SDK本地部署与IK自检.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/service_s2_022_定义IK与MCAP_B数据契约.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/service_s2_023_实现common_frame到robot_base坐标转换.md`
4. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/service_s2_024_实现RM65_SDK_IK求解适配器.md`

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
11. `DOCS/02_约束/阶段二任务体系/L3现有实现盘点约束.md`

### 必读代码

1. `src/data_clean/service/mcap_io.py`
2. `src/data_clean/repo/ros2_codec.py`
3. `src/data_clean/runtime/`
4. `src/data_clean/ui/`
5. `start_data_clean.sh`

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
| 对应功能检验项 | `scene2_ik_mcap_b_writer` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 是 |
| 是否需要写测试产物 | 是；MCAP_B、IK summary、运行日志 |
| 是否需要写运行日志 | 是；最低字段：输入、外参、SDK 来源、IK 统计、输出位置、错误信息 |
| 是否允许临时覆盖配置 | 是；外参、初始关节角、输出目录、覆盖策略 |
| 是否允许保存覆盖到配置文件 | 默认否；仅开发者明确选择时允许 |
| 最终人工验收提示 | 用户运行 `./start_data_clean.sh --dev` 选择场景二和 `scene2_ik_mcap_b_writer` |

## 14. 允许修改

- `src/data_clean/repo/`
- `src/data_clean/service/`
- `src/data_clean/runtime/`
- `src/data_clean/ui/`
- `src/data_clean/tests/`
- `start_data_clean.sh`
- 当前 L3 文件自身

## 15. 禁止修改

- 不修改 MCAP_A 语义。
- 不把失败帧写成 NaN JointState。
- 不让 UI 直接读写 MCAP。
- 不写共享执行记录或当前进度。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "mcap_b or ik_solve_summary or scene2_ik_mcap_b_writer"
```

## 17. 成功标准

- [ ] MCAP_B 写出器只写成功 IK 帧。
- [ ] `IkSolveSummary` 覆盖所有输入 pose。
- [ ] MCAP_B 可读取并包含左右 JointState topic。
- [ ] 开发者入口 `scene2_ik_mcap_b_writer` 可生成隔离 run 产物和运行日志。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

完成后归档到：

```text
DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/
```

