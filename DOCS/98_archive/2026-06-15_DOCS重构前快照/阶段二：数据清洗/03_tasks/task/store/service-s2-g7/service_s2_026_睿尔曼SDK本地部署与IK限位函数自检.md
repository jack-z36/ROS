# L3 微元任务：睿尔曼 SDK 本地部署与 IK 限位函数自检

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：关节限制检查器
L3 编号：service_s2_026
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_026_睿尔曼SDK本地部署与IK限位函数自检.md`
任务类别：数据读写类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_026
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g7/service_s2_026_睿尔曼SDK本地部署与IK限位函数自检.md
  group: service-s2-g7
  branch: service-s2
  wave: 1
  parallel_group: service-s2-g7-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [service_s2_027]
  blocks: [service_s2_028, service_s2_029]
  conflict_scope:
    files: [vendor/RealManRobot/, src/data_clean/tests/]
    modules: []
    config_keys: [realman_sdk]
  dispatch_status: ready
```

## 3. 本次目标

```text
让无上下文 Agent 能自动拉取睿尔曼官方 SDK、安装算法 Demo 依赖、初始化 R65M/RM65 6DOF Algo，并运行 IK、关节角限位和速度限位 smoke test。
```

## 4. 本次不做

- 不实现业务 IK 求解适配器。
- 不实现关节限制检查器业务逻辑。
- 不修改开发者入口菜单。

## 5. 执行对象

- 官方 SDK 缓存：`vendor/RealManRobot/RM_API2/`
- SDK 自检脚本或测试：`src/data_clean/tests/`
- 官方 Demo：`RMDemo_AlgoInterface`

## 6. 执行依赖

- 当前分支必须是 `service-s2`。
- 网络可访问 `https://github.com/RealManRobot/RM_API2.git`。
- Python 命令必须使用 `python3`。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：无项目内直接上游，依赖睿尔曼官方 SDK。
上游接口定义位置：
- DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintConfig.md
- https://github.com/RealManRobot/RM_API2
- https://develop.realman-robotics.com/en/robot/demo/python/algoInterface/
- https://develop.realman-robotics.com/en/robot4th/apipython/classes/algo/
当前 L3 期望消费的字段 / 文件 / 返回值：
- Robotic_Arm.rm_robot_interface 可导入
- Algo(RM_MODEL_RM_65_E, RM_MODEL_RM_B_E) 可初始化
- rm_algo_inverse_kinematics 可调用
- rm_algo_ikine_check_joint_position_limit 可调用
- rm_algo_ikine_check_joint_velocity_limit 可调用
是否存在接口冲突：未知，必须通过自检发现。
如果有冲突，本次处理策略：写清稳定失败原因，不改业务模块。
```

## 8. 预期改动形态

- 新增 SDK 自检脚本或测试，能在 SDK 已安装或已克隆后运行。
- `vendor/RealManRobot/RM_API2/` 只作为本地缓存，不进入 Git。
- 执行摘要记录 SDK 来源、Demo 路径、导入结果、IK 返回码、限位函数返回码。

## 9. 读写输出

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 覆盖策略 |
|---|---|---|---|
| 克隆官方 SDK | `https://github.com/RealManRobot/RM_API2.git` | `vendor/RealManRobot/RM_API2/` | 已存在时复用并校验，不删除 |
| 搜索 Demo | `vendor/RealManRobot/RM_API2/` | 包含 `RMDemo_AlgoInterface` 的目录 | 硬编码路径不存在时必须搜索 |
| 安装依赖 | Demo `requirements.txt` | 当前 Python 环境 | 不创建新虚拟环境 |
| 运行自检 | SDK import / Algo / IK / limit functions | 测试输出或执行摘要 | 失败也必须写明原因 |

## 10. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/关节限制检查器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/JointConstraintConfig.md`
3. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`

### 必读相关微元任务记录

1. `DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g6/service_s2_021_建立睿尔曼SDK本地部署与IK自检.md`
2. 如果存在，读取 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/` 下 SDK / IK 相关已完成任务。

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

1. `.gitignore`
2. `src/data_clean/tests/`

## 11. TDD 执行要求

执行前必须先运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及测试新增时必须使用 `$tdd`。

## 12. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | 不直接接入开发者入口，但由 `scene2_joint_constraint_check` 间接覆盖 |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 是；SDK 自检结果 |
| 是否需要写运行日志 | 是；SDK 来源、Demo 路径、导入结果、IK 返回码、限位函数返回码、错误信息 |
| 是否允许临时覆盖配置 | 否 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 场景最终验收仍需用户运行 `./start_data_clean.sh --dev` |

## 13. 允许修改

- `src/data_clean/tests/`
- 必要时新增合规的 SDK 自检脚本。
- 当前 L3 文件自身。

## 14. 禁止修改

- 不修改业务 IK 求解器。
- 不修改 MCAP_A / MCAP_B 写出逻辑。
- 不提交 `vendor/RealManRobot/RM_API2/` 内容。

## 15. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
git clone https://github.com/RealManRobot/RM_API2.git vendor/RealManRobot/RM_API2
python3 -m pip install -r <搜索到的RMDemo_AlgoInterface目录>/requirements.txt
python3 <搜索到的RMDemo_AlgoInterface目录>/src/main.py
python3 -m pytest src/data_clean/tests/ -k "realman or ik_smoke or joint_limit"
```

如果 Demo 路径不存在，必须先搜索 `RMDemo_AlgoInterface` 后再运行，不得硬编码失败。

## 16. 成功标准

- [ ] SDK 官方仓库已克隆或已复用，且未进入 Git。
- [ ] Python SDK 可导入，或失败原因明确。
- [ ] R65M/RM65 6DOF `Algo` 可初始化，或失败原因明确。
- [ ] IK smoke 已调用 `rm_algo_inverse_kinematics` 并记录返回码。
- [ ] 已调用 `rm_algo_ikine_check_joint_position_limit` 并记录返回码。
- [ ] 已调用 `rm_algo_ikine_check_joint_velocity_limit` 并记录返回码。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系。

## 17. 完成后交接

完成后勾选成功标准，追加执行摘要，并将本文件归档到：

```text
DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g7/
```

