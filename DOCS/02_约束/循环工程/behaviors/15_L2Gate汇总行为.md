# L2 Gate 汇总行为

## 消费 Agent

- L2 Gate agent

## 本文职责

本文只约束 L2 Gate agent 如何汇总目标 L2 的 Gate 证据并输出报告。

## 不负责

本文不执行 L3 实现、不生成单个 L3 验收结论、不执行 Git 合并。

## 必须读取

- 目标 L2 dispatch。
- 目标 L2 整体验收卡片。
- 目标 L2 `验收结果.md`。
- 目标 L2 全部 L3 验收日志。
- `00_status/git_sync_status.md`。
- `00_status/hardware_block_status.md`。

## Gate 前置校验

目标 L2 必须同时具备：

- `DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2>/验收结果.md`
- `DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2>/L2整体验收报告.md` 或本次 Gate 将输出该文件
- `DOCS/03_工程/阶段四：模型部署/05_acceptance/<l2>/人类验收清单.md`

如果目标 L2 的 acceptance 只存在于 `05_acceptance/_legacy_layer_based_act/`，或目标 L2 使用旧 ID `l2-01-types`、`l2-02-config`、`l2-03-assembly`、`l2-04-publish`、`l2-05-hardware`，Gate 必须直接失败并报告“旧流程残留”。

## 必须输出

- `05_acceptance/<l2>/L2整体验收报告.md`。
- required L3 状态汇总。
- L2 运行场景覆盖情况。
- blocked 项及是否可接受。
- 是否允许进入下游 L2。
- 是否允许合入 `model_deploy`。

## 禁止事项

- 禁止伪造未运行命令。
- 禁止把真机 blocked 写成 real-robot 通过。
- 禁止自行执行 Git 合并。
- 禁止从 legacy acceptance 目录生成当前 L2 Gate 结论。
