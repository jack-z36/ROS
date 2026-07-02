# Scene1DevRunLog

## 定义

`Scene1DevRunLog` 是场景一开发者功能检验的机器可读运行日志，记录输入、配置、执行步骤、关键状态、错误信息和输出位置。

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `run_id` | string | 对应 [[Scene1DevRun]] |
| `check_id` | string | 对应 [[Scene1DevCheckItem]] |
| `input` | object | 小样本输入与选择方式 |
| `config_path` | path | 默认生产配置来源 |
| `effective_config` | path | 本次运行配置快照 |
| `overrides` | list | 本次 [[Scene1DevConfigOverride]] |
| `steps` | list | 执行步骤和状态 |
| `artifacts` | list | 输出 [[Scene1DevArtifact]] |
| `status` | enum | `success` / `failed` / `skipped` |
| `error` | string/null | 失败原因 |

## 有效性规则

- 每个 dev 功能检验和 smoke test 必须写出运行日志。
- 日志必须能定位输出产物位置。
- 失败时必须记录错误信息，不允许只在终端打印后丢失。

## 相关链接

- [[Scene1DevRun]]
- [[Scene1DevArtifact]]
- [[Scene1DevConfigOverride]]
