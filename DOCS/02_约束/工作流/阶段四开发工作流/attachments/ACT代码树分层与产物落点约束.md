# ACT 代码树分层与产物落点约束

> [!info] 归属
> - 类型：架构落点约束（阶段四 · ACT 代码树专用）
> - 目标路径：`DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`
> - 上游原则：[[架构边界与机械约束原则]]（第四节「默认层次模型」、第三节「数据 shape 边界校验」、第六节「依赖方向」）
> - 适用对象：阶段四 ACT 代码树（`src/model_deploy/act/`）下所有源码、配置、launch、测试、脚本产物的落点
> - 强制性：L2 / L3 执行时必须遵守。产物落点不符合本约束，视为 L3 未完成。

## 一、强制分层目录结构

ACT 代码树（`src/model_deploy/act/`）必须按以下六层目录组织。目录名固定，不得自创别名、不得合并、不得省略：

```text
src/model_deploy/act/
├── types/              # 层 1：Types —— 数据结构与常量
├── config/             # 层 2：Config —— 配置定义
├── repo/               # 层 3：Repo —— 外部资源读写边界
├── service/            # 层 4：Service —— 业务逻辑
├── runtime/            # 层 5：Runtime —— 节点装配与调度
├── ui/                 # 层 6：UI —— 对外接口（ROS topic 发布）
├── launch/             # launch 文件（跨层装配入口）
├── config_files/       # 运行配置实例（.yaml）
└── tests/              # 测试（顶层集中，按层分子目录）
```

> [!warning] 分层目录名固定
> 六个分层目录名 `types / config / repo / service / runtime / ui` 不得改动。这与《架构边界与机械约束原则》第四节的默认层次模型一一对应，是依赖方向检查的基础。

## 二、各层职责与允许落点

### 层 1 · `types/`（地基，不依赖任何层）

| 项 | 内容 |
|---|---|
| 职责 | 定义稳定数据结构、维度常量、段序定义、编解码函数、枚举、结果对象。 |
| 允许放置 | `state_codec.py`、`action_codec.py`、`action_spec.py`、维度常量、segment 定义、TypedDict/dataclass。 |
| 禁止放置 | 配置读取、文件 IO、ROS 消息、硬件 SDK、业务逻辑。 |
| 依赖方向 | **不依赖** config / repo / service / runtime / ui。只能依赖标准库和 numpy 等基础库。 |
| 对应 L2 | L2-01 |

### 层 2 · `config/`（依赖 types）

| 项 | 内容 |
|---|---|
| 职责 | 配置 schema 定义、配置加载、配置校验。产出可被下游消费的有效配置对象。 |
| 允许放置 | `schema.py`（frozen dataclass）、配置加载器、配置校验逻辑。 |
| 禁止放置 | 业务计算、ROS 节点、硬件调用、模型推理。 |
| 依赖方向 | 依赖 `types/`（引用维度常量）。**不依赖** repo/service/runtime/ui。 |
| 对应 L2 | L2-02 |
| 配置实例 | `.yaml` 配置文件**不放此处**，放 `config_files/`（见第五节）。 |

### 层 3 · `repo/`（依赖 types + config）

| 项 | 内容 |
|---|---|
| 职责 | 外部资源读写边界：模型 bundle 加载、normalizer 读取、checkpoint 反序列化、manifest 解析。 |
| 允许放置 | `policy_loader.py`（ACT checkpoint 加载）、`bundle_reader.py`、`manifest_parser.py`。 |
| 禁止放置 | 业务逻辑、ROS topic 订阅发布、硬件 SDK 调用。 |
| 依赖方向 | 依赖 `types/`、`config/`。横切能力（bundle）通过显式 loader 接入，业务层不散落读取（第五节原则）。 |
| 对应 L2 | L2-03 |

### 层 4 · `service/`（依赖 types + config + repo）

| 项 | 内容 |
|---|---|
| 职责 | 业务逻辑：observation snapshot 装配、batch 构建、安全检查、action 转换。 |
| 允许放置 | `observation_collector.py`、`safety_guard.py`、`batch_builder.py`、action 转换逻辑。 |
| 禁止放置 | ROS 节点生命周期、timer/executor、直接硬件发送、直接读 bundle 文件（走 repo）。 |
| 依赖方向 | 依赖 `types/`、`config/`、`repo/`。**不依赖** runtime/ui。 |
| 对应 L2 | L2-03（observation_collector）、L2-04（safety_guard） |

### 层 5 · `runtime/`（依赖 types + config + service）

| 项 | 内容 |
|---|---|
| 职责 | 运行时调度：控制循环、推理工作线程、latest-only 缓冲、生命周期管理。 |
| 允许放置 | `control_loop.py`、`inference_worker.py`、`shared_buffer.py`、调度器。 |
| 禁止放置 | 业务计算（走 service）、直接 ROS topic 发布（走 ui）。 |
| 依赖方向 | 依赖 `types/`、`config/`、`service/`。**不依赖** ui。 |
| 对应 L2 | L2-04 |

### 层 6 · `ui/`（依赖全部下游层）

| 项 | 内容 |
|---|---|
| 职责 | 对外接口：ROS 节点装配、topic 订阅/发布、消息转换、launch 入口封装。 |
| 允许放置 | `ros_nodes/`（`act_vla_deploy_node.py`、`command_bridge_sender_node.py`、`rm65_driver_node.py`、`elephant_gripper_node.py`）、publisher/subscriber 创建、消息适配。 |
| 禁止放置 | 核心业务计算（走 service）、模型推理实现（走 repo/service）。 |
| 依赖方向 | 可依赖 `types/`、`config/`、`service/`、`runtime/`。是最外层，不被其他层依赖（launch 除外）。 |
| 对应 L2 | L2-04（act_vla_deploy_node）、L2-05（command_bridge/驱动节点） |

## 三、跨层产物落点

### `launch/`

| 项 | 内容 |
|---|---|
| 职责 | ROS2 launch 文件，跨层装配节点。 |
| 允许放置 | `act_rm65_deploy.launch.py`。 |
| 归属 | 不属于单一层（它是装配入口），独立成目录。对应 L2-05。 |

### `config_files/`

| 项 | 内容 |
|---|---|
| 职责 | 运行配置实例（`.yaml`），被 `config/schema.py` 加载。 |
| 允许放置 | `deploy.yaml`、`paths.yaml`。 |
| 归属 | 配置 schema（定义）放 `config/`，配置实例（值）放 `config_files/`。分离定义与实例。 |

> [!note] 为什么 config 定义和实例分离
> `config/schema.py` 是代码（frozen dataclass，需测试、走 L2-02 单测）；`deploy.yaml` 是数据（运行时值，按部署环境变）。混在一起会让"改配置值"和"改配置结构"的 L3 边界模糊。分离后，schema 变动走 L2-02，yaml 值调整可独立。

## 四、测试产物落点（顶层集中）

测试**不在各分层目录内嵌**，统一集中在 `act/tests/` 下，按分层分子目录（与源码六层一一对应）：

```text
src/model_deploy/act/tests/
├── types/                  # L2-01 单测
│   ├── test_state_codec.py
│   ├── test_action_codec.py
│   └── test_action_spec.py
├── config/                 # L2-02 单测
│   └── test_config.py
├── repo/                   # L2-03 单测（policy_loader）
│   └── test_policy_loader.py
├── service/                # L2-03/L2-04 单测
│   ├── test_observation_collector.py
│   └── test_safety_guard.py
├── runtime/                # L2-04 单测
│   └── test_control_loop.py
├── ui/                     # L2-04/L2-05 单测
│   └── test_deploy_node.py
├── integration/            # 跨层集成测试（dry-run 全链路）
│   └── test_dry_run.py
└── shadow/                 # shadow-run 集成测试
    └── test_shadow_run.py
```

### 测试落点规则

| 测试类型 | 落点 | 命名 |
|---|---|---|
| types 层单测 | `tests/types/test_<被测模块>.py` | `test_state_codec.py` |
| config 层单测 | `tests/config/test_config.py` | — |
| repo 层单测 | `tests/repo/test_<被测模块>.py` | `test_policy_loader.py` |
| service 层单测 | `tests/service/test_<被测模块>.py` | `test_safety_guard.py` |
| runtime 层单测 | `tests/runtime/test_<被测模块>.py` | `test_control_loop.py` |
| ui 层单测 | `tests/ui/test_<被测模块>.py` | `test_deploy_node.py` |
| 跨层集成测试 | `tests/integration/` | `test_dry_run.py` |
| shadow-run 测试 | `tests/shadow/` | `test_shadow_run.py` |
| 公共 fixture | `tests/conftest.py`（顶层）或 `tests/<层>/conftest.py` | — |

> [!warning] 测试文件禁止内嵌到源码分层目录
> `types/state_codec.py` 的测试**不放** `types/tests/test_state_codec.py`，**只放** `tests/types/test_state_codec.py`。这是硬约束，沿用 pi05 顶层集中惯例。违反则 pytest 收集范围混乱、L2 Gate 命令无法按层过滤。

### L2 Gate 的 pytest 命令按层过滤

```bash
# L2-01 Gate 只跑 types 层测试
pytest src/model_deploy/act/tests/types/ -v

# L2-02 Gate 只跑 config 层测试
pytest src/model_deploy/act/tests/config/ -v

# L2-03 Gate 跑 repo + service 输入侧
pytest src/model_deploy/act/tests/repo/ src/model_deploy/act/tests/service/ -v

# 集成测试（dry-run）
pytest src/model_deploy/act/tests/integration/ -v
```

## 五、L3 产物落点速查表

每个 L3 执行时产出的产物，按下表落到唯一位置：

| 产物类型 | 唯一落点 | 示例 | 禁止落点 |
|---|---|---|---|
| types 层源码 | `src/model_deploy/act/types/` | `state_codec.py` | 其他分层、tests/ |
| config 层源码（schema） | `src/model_deploy/act/config/` | `schema.py` | config_files/、其他分层 |
| repo 层源码 | `src/model_deploy/act/repo/` | `policy_loader.py` | service/、其他分层 |
| service 层源码 | `src/model_deploy/act/service/` | `safety_guard.py` | runtime/、ui/ |
| runtime 层源码 | `src/model_deploy/act/runtime/` | `control_loop.py` | ui/ |
| ui 层源码（ROS 节点） | `src/model_deploy/act/ui/ros_nodes/` | `act_vla_deploy_node.py` | runtime/、service/ |
| launch 文件 | `src/model_deploy/act/launch/` | `act_rm65_deploy.launch.py` | ui/、其他分层 |
| 配置实例（.yaml） | `src/model_deploy/act/config_files/` | `deploy.yaml` | config/（schema 目录） |
| 单测 | `src/model_deploy/act/tests/<层>/` | `tests/types/test_state_codec.py` | 源码分层目录内 |
| 集成测试 | `src/model_deploy/act/tests/integration/` | `test_dry_run.py` | tests/types/ 等单测目录 |
| shadow-run 测试 | `src/model_deploy/act/tests/shadow/` | `test_shadow_run.py` | integration/ |
| 公共 fixture | `src/model_deploy/act/tests/conftest.py` | — | 各层内 |
| L2/L3 验收脚本 | `DOCS/.../05_acceptance/<l2>/scripts/` | `dry_run_check.py` | src/ 下 |
| 验收日志 | `DOCS/.../05_acceptance/<l2>/logs/` | `gate_output.txt` | src/ 下 |
| 验收结果/签字 | `DOCS/.../05_acceptance/<l2>/验收结果.md` | — | scripts/、logs/ |

## 六、依赖方向不变量（可机械检查）

下列依赖关系是硬约束，违反即架构污染：

```text
types    → （无下游依赖）
config   → types
repo     → types, config
service  → types, config, repo
runtime  → types, config, service
ui       → types, config, service, runtime
```

**禁止反向依赖**：
- types 不得 import config/repo/service/runtime/ui。
- config 不得 import repo/service/runtime/ui。
- repo 不得 import service/runtime/ui。
- service 不得 import runtime/ui。
- runtime 不得 import ui。

> [!note] 升级为机械检查的路径
> 本节依赖方向可逐步升级为 import 结构测试（如 `pytest-import-check` 或自定义 import graph test）。在未机械化前，L3 执行时按文档校验，L2 Gate review 时复核。反复违反时登记为 lint/结构测试候选（对照《架构边界与机械约束原则》第一节、第八节）。

## 七、L3 任务文件中的落点声明

每个 L3 任务文件（按《L3微元改造任务模板》）在「允许修改」章节必须显式声明本任务的产物落点，格式：

```text
本次产物落点：
- 源码：src/model_deploy/act/types/state_codec.py
- 测试：src/model_deploy/act/tests/types/test_state_codec.py
- 配置（如有）：src/model_deploy/act/config_files/<name>.yaml
- 验收脚本（如有）：DOCS/.../05_acceptance/l2-01-types/scripts/<name>.py
```

验收 sub-agent 检查时，若实际产物路径与本声明不符，判 `FAIL_LOCAL`。

## 八、违反处理

| 违反情形 | 处理 |
|---|---|
| 源码放错分层（如 safety_guard 放 runtime/） | L3 验收判 FAIL_LOCAL，要求移到 service/ |
| 测试内嵌到源码目录 | L3 验收判 FAIL_LOCAL，要求移到 tests/<层>/ |
| 配置实例放 config/（schema 目录） | L3 验收判 FAIL_LOCAL，要求移到 config_files/ |
| 存在反向 import | L3 验收判 FAIL_LOCAL，登记为结构测试候选 |
| 产物路径与 L3 声明不符 | L3 验收判 FAIL_LOCAL |
