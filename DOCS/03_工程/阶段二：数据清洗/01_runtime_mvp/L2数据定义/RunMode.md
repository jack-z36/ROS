# RunMode

## 定义

`RunMode` 是 Runtime 运行模式枚举，用于区分开发者检验和用户生产、单场景和全流程。

## 所属位置

阶段二：数据清洗 / L1：runtime_mvp / L2：[[01_Runtime运行上下文定义]]

## 现实语义

`RunMode` 回答“这次运行是给开发者调试用，还是给用户生产用；是只跑一个场景，还是跑完整阶段二 pipeline”。

## 字段或取值

| 取值 | 语义 |
| --- | --- |
| `dev_single_scene` | 开发者端运行单个场景或单个场景 smoke test。 |
| `dev_full_pipeline` | 开发者端运行 fake 全流程 smoke test。 |
| `prod_single_scene` | 用户端生产模式运行单个完整场景。 |
| `prod_full_pipeline` | 用户端生产模式运行阶段二全流程。 |

## 有效性规则

- 只能使用本文列出的受控取值。
- `dev_full_pipeline` 和 `prod_full_pipeline` 必须按 [[SceneName]] 的阶段二顺序执行。
- 开发者模式产物必须与正式生产产物隔离。

## 上游来源

- `./start_data_clean.sh --dev` 进入开发者端模式。
- `./start_data_clean.sh` 进入用户端生产模式。
- UI 或入口层根据用户选择单场景或全流程后传入 Runtime。

## 下游消费者

- [[RunContext]]
- Run 目录管理模块。
- 配置预检查模块。
- 输入产物预检查模块。
- 场景注册与 Service 调度模块。
- Runtime smoke test 模块。

## 不负责

- 不决定具体调用 fake service 还是真实 service；该语义由 [[ServiceMode]] 承载。
- 不承载具体场景名；场景由 [[SceneName]] 承载。
- 不描述业务算法。

## 当前未知问题

| 问题 | 为什么重要 | 当前处理方式 | 需要谁确认 |
| --- | --- | --- | --- |
| 生产模式是否允许附带调试输出 | 影响正式产物和调试产物隔离策略。 | 第一版按文件存放规范隔离输出。 | Run 目录管理模块设计时确认。 |

## 相关链接

- [[RunContext]]
- [[ServiceMode]]
- [[SceneName]]
- [[01_Runtime运行上下文定义]]

