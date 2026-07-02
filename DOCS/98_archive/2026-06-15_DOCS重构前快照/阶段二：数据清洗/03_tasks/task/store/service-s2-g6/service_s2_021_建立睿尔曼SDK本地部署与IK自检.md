# L3 微元任务：建立睿尔曼 SDK 本地部署与 IK 自检

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景二：硬件数据可靠性验证
L1：service_s2
L2 能力：IK 求解与 MCAP_B 生成器
L3 编号：service_s2_021
当前任务文件路径：`DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g6/service_s2_021_建立睿尔曼SDK本地部署与IK自检.md`
任务类别：数据读写类
来源 L2 文件：`DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`

## 2. 调度元数据

```yaml
dispatch:
  task_id: service_s2_021
  task_file: DOCS/阶段二：数据清洗/03_tasks/task/active/service-s2-g6/service_s2_021_建立睿尔曼SDK本地部署与IK自检.md
  group: service-s2-g6
  branch: service-s2
  wave: 1
  parallel_group: service-s2-g6-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [service_s2_024, service_s2_025]
  conflict_scope:
    files: [vendor/RealManRobot/, src/data_clean/tests/]
    modules: []
    config_keys: [realman_sdk]
  dispatch_status: ready
```

## 3. 本次目标

```text
让无上下文 Agent 能自动拉取睿尔曼官方 SDK、安装 Demo 依赖、导入 Python SDK，并运行一次 RM65 IK smoke test。
```

## 4. 本次不做

- 不实现本项目 IK 业务适配器。
- 不写 MCAP_B。
- 不修改场景二开发者菜单。

## 5. 执行对象

- 官方 SDK 克隆缓存：`vendor/RealManRobot/RM_API2/`
- SDK 自检脚本或测试：`src/data_clean/tests/`
- 官方 Demo：`RMDemo_AlgoInterface`

## 6. 执行依赖

- 当前分支必须是 `service-s2`。
- 网络可访问 `https://github.com/RealManRobot/RM_API2.git`，如网络失败应明确汇报。
- Python 命令必须使用 `python3`。

## 7. 上游接口确认

```text
本 L3 直接依赖的上游功能：无直接上游功能，依赖睿尔曼官方 SDK。
上游接口定义位置：
- https://github.com/RealManRobot/RM_API2
- https://develop.realman-robotics.com/en/robot/demo/python/algoInterface/
- https://develop.realman-robotics.com/en/robot4th/apipython/classes/algo/
当前 L3 期望消费的字段 / 文件 / 返回值：
- Robotic_Arm.rm_robot_interface 可导入
- Algo 可初始化
- rm_algo_inverse_kinematics 可调用
是否存在接口冲突：未知，需通过自检发现。
如果有冲突，本次处理策略：只写清稳定失败原因，不改业务模块。
```

## 8. 预期改动形态

- `.gitignore` 已允许 `vendor/RealManRobot/` 不进 Git。
- 仓库内出现 SDK 自检测试或脚本，能在 SDK 已安装或已克隆后运行。
- 执行摘要中记录 SDK 来源、路径、版本或 commit、IK smoke 结果。

## 9. 读写输出

### 读写动作

| 动作 | 输入路径 / 来源 | 输出路径 / 目标 | 格式 | 覆盖策略 |
|---|---|---|---|---|
| 克隆官方 SDK | `https://github.com/RealManRobot/RM_API2.git` | `vendor/RealManRobot/RM_API2/` | Git repo | 已存在时不删除，先复用并校验 |
| 查找 Demo | `vendor/RealManRobot/RM_API2/` | `RMDemo_AlgoInterface` 路径 | 目录 | 如果硬编码路径不存在，先搜索 |
| 安装依赖 | Demo `requirements.txt` | 当前 Python 环境 | pip packages | 不创建新虚拟环境 |
| 记录自检 | SDK import / IK smoke | 测试输出或执行摘要 | text / JSON | 失败也必须写明原因 |

### 文件或目录结构

```text
vendor/
└── RealManRobot/
    └── RM_API2/              # 不进 Git

src/data_clean/tests/
└── ...                       # SDK 自检测试或脚本，不进 Git
```

## 10. 数据读写验收重点

- `vendor/RealManRobot/RM_API2/` 可由官方仓库克隆或已存在复用。
- 能找到 `RMDemo_AlgoInterface`，路径变化时先搜索。
- `from Robotic_Arm.rm_robot_interface import *` 可导入，或失败原因明确。
- 能初始化 RM65 `Algo`，并调用一次 `rm_algo_inverse_kinematics`。
- IK smoke 使用官方示例 pose，返回成功或稳定失败码，不能只测试 import。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/阶段二：数据清洗/02_service/场景二/L2能力模块/IK 求解与 MCAP_B 生成器.md`
2. `DOCS/阶段二：数据清洗/02_service/场景二/L2数据定义/Rm65IkConfig.md`
3. `DOCS/阶段二：数据清洗/约束文件/文件存放规范.md`

### 必读相关微元任务记录

1. 如果存在，读取 `DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/` 下已完成任务。

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

## 12. TDD 执行要求

执行前必须先运行：

```bash
bash scripts/init_data_clean_dev.sh
```

本 L3 涉及代码或测试新增时必须使用 `$tdd`。

## 13. 开发者验收入口关联

| 项目 | 内容 |
|---|---|
| 统一入口 | `./start_data_clean.sh --dev` |
| 所属一级场景菜单 | 场景二 |
| 对应功能检验项 | `scene2_ik_mcap_b_writer` |
| 是否影响场景完整 smoke test | 是 |
| 是否需要修改开发者入口 / 菜单 / 脚本调用 | 否 |
| 是否需要写测试产物 | 是；SDK 自检结果 |
| 是否需要写运行日志 | 是；最低字段：SDK 来源、Demo 路径、导入结果、IK 返回码、错误信息 |
| 是否允许临时覆盖配置 | 否 |
| 是否允许保存覆盖到配置文件 | 默认否 |
| 最终人工验收提示 | 本 L3 完成后，场景最终验收仍需用户运行 `./start_data_clean.sh --dev` |

## 14. 允许修改

- `src/data_clean/tests/`
- 必要时新增 SDK 自检脚本到合规位置。
- 当前 L3 文件自身。

## 15. 禁止修改

- 不修改业务 IK 求解器。
- 不修改 MCAP_A / MCAP_B 写出逻辑。
- 不提交 `vendor/RealManRobot/RM_API2/` 内容。

## 16. 验收命令

```bash
bash scripts/init_data_clean_dev.sh
git clone https://github.com/RealManRobot/RM_API2.git vendor/RealManRobot/RM_API2
python3 -m pip install -r vendor/RealManRobot/RM_API2/Demo/RMDemo_Python/RMDemo_AlgoInterface/requirements.txt
python3 vendor/RealManRobot/RM_API2/Demo/RMDemo_Python/RMDemo_AlgoInterface/src/main.py
python3 -m pytest src/data_clean/tests/ -k "realman or ik_smoke"
```

如果 Demo 路径不存在，必须先用文件搜索定位 `RMDemo_AlgoInterface` 后再运行。

## 17. 成功标准

- [ ] SDK 官方仓库已克隆或已复用，且未进入 Git。
- [ ] Python SDK 可导入，或失败原因明确。
- [ ] RM65 `Algo` 可初始化，或失败原因明确。
- [ ] IK smoke 已调用 `rm_algo_inverse_kinematics` 并记录返回码。
- [ ] 已说明本 L3 与 `./start_data_clean.sh --dev` 开发者验收入口的关系，或说明由哪个功能检验项 / smoke test 间接覆盖。

## 18. 完成后交接

完成后勾选成功标准，追加执行摘要，并将本文件归档到：

```text
DOCS/阶段二：数据清洗/03_tasks/task/completed/03-service-s2/service-s2-g6/
```

