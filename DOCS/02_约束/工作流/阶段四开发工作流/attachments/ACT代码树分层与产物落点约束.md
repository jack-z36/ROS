# ACT 代码树分层与产物落点约束

> [!info] 归属
> - 类型：架构落点约束（阶段四 ACT 代码树专用）。
> - 适用对象：`src/model_deploy/act/` 下的源码、配置、launch、测试和运行脚本。
> - 上游工作流：`../阶段四模型部署程序改造工作流.md`。
> - 强制性：L2/L3 执行时必须遵守。

## 1. 核心判断

L2 是功能模块边界，代码目录是落点边界。一个 L2 可以横跨多个代码层，但每个产物必须落到唯一目录。

```text
L2 != types/config/repo/service/runtime/ui
L2 = 一个运行时功能闭环
六层目录 = 文件职责和依赖方向约束
```

## 2. 强制代码树

```text
src/model_deploy/act/
├── types/
├── config/
├── repo/
├── service/
├── runtime/
├── ui/
├── launch/
├── config_files/
└── tests/
```

不得自创同义目录，不得把测试内嵌到源码目录。

## 3. 六层职责

| 层 | 职责 | 允许放置 | 禁止放置 |
|---|---|---|---|
| `types/` | 数据结构、常量、维度、段序、codec、result 对象 | `action_spec.py`、`state_codec.py`、`action_codec.py` | 配置读取、ROS、硬件、模型加载 |
| `config/` | 配置 schema、配置对象、配置校验 | `schema.py`、配置 dataclass | 业务计算、ROS node、模型推理 |
| `repo/` | 进程外资源读取和反序列化 | bundle reader、manifest parser、normalizer loader、policy loader | ROS topic、硬件 SDK、运行调度 |
| `service/` | RAM 内业务计算、转换、校验 | observation collector、batch builder、safety guard、action adapter | timer、thread、ROS node 生命周期 |
| `runtime/` | 时间、线程、队列、状态机、调度 | shared buffer、inference worker、control loop、chunk cursor state | 直接 ROS 发布、直接硬件发送 |
| `ui/` | 外部交互边界 | ROS node、subscriber、publisher、message converter | 核心模型推理、核心业务计算 |

## 4. 依赖方向

```text
types    -> 无下游依赖
config   -> types
repo     -> types, config
service  -> types, config, repo
runtime  -> types, config, service
ui       -> types, config, repo, service, runtime
```

禁止反向依赖：

- `types/` 不得 import `config/repo/service/runtime/ui`。
- `config/` 不得 import `repo/service/runtime/ui`。
- `repo/` 不得 import `service/runtime/ui`。
- `service/` 不得 import `runtime/ui`。
- `runtime/` 不得 import `ui`。

## 5. 跨层产物

| 产物 | 唯一落点 | 说明 |
|---|---|---|
| ROS launch | `src/model_deploy/act/launch/` | 跨层装配入口。 |
| 配置实例 | `src/model_deploy/act/config_files/` | `.yaml` 运行配置值，不放 `config/`。 |
| 单测 | `src/model_deploy/act/tests/<层>/` | 按被测源码层分目录。 |
| 集成测试 | `src/model_deploy/act/tests/integration/` | 跨层 dry-run / mock 闭环。 |
| shadow-run 测试 | `src/model_deploy/act/tests/shadow/` | 不触发真机的 ROS/topic 验收。 |
| L2/L3 验收脚本 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2>/scripts/` | 不放源码目录。 |
| 验收日志 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2>/logs/` | 命令输出和人工记录。 |

## 6. L3 产物落点声明

每个 L3 必须在任务文件中声明本次产物落点：

```text
本次产物落点：
- 源码：src/model_deploy/act/<层>/<file>.py
- 测试：src/model_deploy/act/tests/<层>/test_<file>.py
- 配置实例：src/model_deploy/act/config_files/<name>.yaml
- launch：src/model_deploy/act/launch/<name>.launch.py
- 验收脚本：DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2>/scripts/<name>.py
```

实际产物路径与声明不符时，L3 验收必须判失败。

## 7. 按 L2 设计六层产物

每个 L2 在完成 Pi0.5 源码范围匹配、3.5 层微元拆解和 ACT 版微元设计确认后，必须生成六层产物设计表：

| 层 | 是否需要 | 文件路径 | 职责 | 输入 | 输出 | 不负责 |
|---|---|---|---|---|---|---|
| types | 是/否 |  |  |  |  |  |
| config | 是/否 |  |  |  |  |  |
| repo | 是/否 |  |  |  |  |  |
| service | 是/否 |  |  |  |  |  |
| runtime | 是/否 |  |  |  |  |  |
| ui | 是/否 |  |  |  |  |  |

没有经过 Pi0.5 源码盘点和该设计表的 L2，不得直接生成 L3。
