# L3 微元任务：实现 RM65 SDK IK 求解适配器

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：IK 求解与 MCAP_B 生成器
L3 编号：service_s2_024
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g6/service_s2_024_实现RM65_SDK_IK求解适配器.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_024
  task_file: DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s2-g6/service_s2_024_实现RM65_SDK_IK求解适配器.md
  group: service-s2-g6
  branch: service-s2
  wave: 3
  parallel_group: service-s2-g6-p3
  depends_on: [service_s2_021, service_s2_022, service_s2_023]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_025]
  conflict_scope:
    files: [src/data_clean/service/, src/data_clean/tests/]
    modules: [data_clean.service]
    config_keys: [scene2.ik_mcap_b.rm65]
  dispatch_status: ready
```

## 3. 本次目标

```text
实现可 mock、可真实 SDK smoke 的 RM65 IK 适配器，将 RobotBaseTcpPose 转换为 Rm65IkSampleResult。
```

## 4. 本次不做

- 不实现 common->base 转换。
- 不写 MCAP_B。
- 不修改开发者入口。

## 5. 执行对象

- [[RobotBaseTcpPose]]
- [[Rm65IkConfig]]
- [[Rm65IkSampleResult]]
- 睿尔曼 SDK `Algo`

## 6. 执行依赖

- `service_s2_021` SDK 自检已完成。
- `service_s2_022` 数据契约已完成。
- `service_s2_023` common->base 转换已完成。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：common_frame 到 robot_base 坐标转换、睿尔曼 SDK 自检。
上游接口定义位置：
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/RobotBaseTcpPose.md
- DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/Rm65IkConfig.md
当前 L3 期望消费的字段 / 文件 / 返回值：base-frame TCP pose、left/right 初始关节角、SDK Algo。
是否存在接口冲突：无已知冲突。
如果有冲突，本次处理策略：不改坐标转换输出，适配器侧报明确错误。
```

## 8. 预期改动形态

- `src/data_clean/service/` 新增 RM65 IK 适配器。
- 支持依赖注入 / mock SDK。
- 输出逐样本 `Rm65IkSampleResult`，失败帧不推进 seed。
- 测试覆盖 seed 连续策略和 SDK 状态码映射。

## 9. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 第一帧合法 pose | 使用配置初始关节角作为 `q_in` 调 SDK | `status=success` 或 SDK 失败 | SDK 返回码 |
| 后续成功 | 使用上一成功 `joint_deg` 作为 seed | 推进 seed | 无 |
| IK 失败 | 不推进 seed，不输出关节角 | `status=failed` | `ik_failed` |
| SDK 缺失 | import 或初始化失败 | 整体失败或 `sdk_error` | `realman_sdk_import_failed` / `realman_sdk_api_missing` |
| 输入非法 | 四元数非法或字段缺失 | `invalid_input` | `invalid_pose_quaternion` |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `arm_side` | string | left/right | 与输入一致 |
| `seed_joint_deg` | float[6] | 本帧 q_in | 长度 6 |
| `joint_deg` | float[6]/null | 输出关节角 | 成功时存在 |
| `status` | string | IK 状态 | 稳定枚举 |
| `sdk_return_code` | int/null | SDK 返回码 | 调用 SDK 时记录 |

## 10. 数据计算验收重点

- mock SDK 能覆盖成功和失败。
- 真实 SDK smoke 不阻塞 mock 单元测试；真实 SDK 缺失时给出 skip 或明确失败。
- seed 连续策略符合 L2：失败帧不推进。
- 左右臂 seed 和状态互不污染。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/Rm65IkConfig.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景二/L2数据定义/Rm65IkSampleResult.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/service_s2_021_建立睿尔曼SDK本地部署与IK自检.md`
2. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/service_s2_022_定义IK与MCAP_B数据契约.md`
3. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/service_s2_023_实现common_frame到robot_base坐标转换.md`

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
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 否 |
| 是否需要写运行日志 | 是；SDK 调用状态由后续入口记录 |
| 是否允许临时覆盖配置 | 是；初始关节角仅本次运行生效 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 由 `scene2_ik_mcap_b_writer` 间接覆盖 |

## 14. 允许修改

- `src/data_clean/service/`
- `src/data_clean/tests/`
- 当前 L3 文件自身

## 15. 禁止修改

- 不修改坐标转换函数契约。
- 不写 MCAP_B。
- 不改开发者入口。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
python3 -m pytest src/data_clean/tests/ -k "rm65_ik or ik_adapter"
```

如果真实 SDK 可用，补充运行：

```bash
python3 -m pytest src/data_clean/tests/ -k "realman and ik_smoke"
```

## 17. 成功标准

- [ ] RM65 IK 适配器可被 mock SDK 测试。
- [ ] 第一帧使用初始 seed。
- [ ] 成功帧推进 seed，失败帧不推进 seed。
- [ ] 左右臂独立求解和独立 seed。
- [ ] SDK 返回码映射为稳定 failure reason。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

完成后归档到：

```text
DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/
```

