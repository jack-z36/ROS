# 真机阻塞状态

## 消费 Agent

- 主 Agent
- L2 Gate agent

## 本文职责

本文只记录阶段四无真机循环中的硬件 blocked 条件、real-robot 交接条件和真机风险边界。

## 不负责

本文不记录软件 L3 进度，不替代 `l2-04-safety-guard`、`l2-05-action-publisher` 或 `l2-06-control-loop` 验收结果，也不提供真机执行命令全文。

## 当前硬件边界

当前开发环境按无外设环境处理。任何 real-robot 行为都不得在未满足现场条件时写成通过。

## real-robot blocked 条件

任何 real-robot smoke test 或真实执行器发送默认保持 blocked。解除 blocked 必须同时满足：

- 新版 `l2-01-external-contract` 至 `l2-06-control-loop` 的软件侧 Gate 和人类验收均通过，或当前 L2 明确声明只做分段真机验证。
- RM65 双臂连接、标定和工作空间确认完成。
- 大象夹爪连接、标定和 width 映射确认完成。
- 真模型 bundle 就绪。
- 物理急停和 deadman 可用。
- 人在场并完成安全区域清空。
- 用户或现场负责人明确授权。
- 回滚路径和停止策略已确认。

## 允许声明

- 允许声明 shadow-run、dry-run 或静态评审通过。
- 允许声明 real-robot blocked 且交接条件完整。

## 禁止声明

- 禁止在无硬件环境下声明 real-robot smoke test 通过。
- 禁止伪造 SDK 返回码、动作观察结果或急停验证结果。
- 禁止引用旧 `deploy_022` / `deploy_023` 作为当前循环目标或放行条件。
