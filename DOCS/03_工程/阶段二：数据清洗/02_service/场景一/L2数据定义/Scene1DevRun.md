# Scene1DevRun

## 定义

`Scene1DevRun` 是场景一开发者功能检验或完整 smoke test 的一次独立运行目录，用于隔离调试产物和运行日志，避免污染正式生产输出。

## 推荐目录结构

```text
asset/阶段二：数据清洗/dev_runs/scene1/<timestamp>_<check_id>/
├── artifacts/
├── logs/
│   └── run_log.json
└── config/
    ├── effective_config.yaml
    └── overrides.json
```

## 字段或取值

| 字段 | 类型 | 现实含义 |
|---|---|---|
| `run_id` | string | 单次开发调试运行 ID |
| `check_id` | string | 对应 [[Scene1DevCheckItem]] |
| `run_dir` | path | 独立运行目录 |
| `artifact_dir` | path | 测试产物目录 |
| `log_dir` | path | 运行日志目录 |
| `effective_config` | path | 本次实际使用配置快照 |
| `status` | enum | `success` / `failed` / `skipped` |

## 有效性规则

- 每次功能检验必须创建独立 `run_dir`。
- 测试产物不得写入正式 canonical dataset 目录。
- 调试输出不得覆盖生产 cleaned/canonical 输出。
- `run_dir` 内至少包含测试产物和运行日志。

## 相关链接

- [[Scene1DevCheckItem]]
- [[Scene1DevArtifact]]
- [[Scene1DevRunLog]]
