# L2 Gate 行为约束

## 消费 Agent

- L2 Gate agent

## 本文职责

本文只说明 L2 Gate agent 汇总目标 L2 时必须消费哪些原子行为约束文件。

## 不负责

本文不承载 L2 Gate 汇总规则正文、L3 验收规则、任务分配规则或 Git 合并规则。

## 角色定位

L2 Gate agent 只负责目标 L2 的 Gate 汇总报告，判断场景覆盖、blocked 项、下游放行和合入建议。

## 必读行为文件

| 顺序 | 行为 | 必读文件 |
|---|---|---|
| 1 | L2 Gate 汇总 | `behaviors/15_L2Gate汇总行为.md` |

## 禁止事项

- 禁止只读取本文就执行 Gate。
- 禁止 L2 Gate agent 执行 Git 合并。
- 禁止在本文补写具体行为规则；新增 Gate 行为必须新增 `behaviors/` 原子文件。

