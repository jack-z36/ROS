# 主 Agent 行为约束

## 消费 Agent

- 主 Agent

## 本文职责

本文只说明主 Agent 在 Ralph / OpenCode L2 循环中必须消费哪些原子行为约束文件。

## 不负责

本文不承载状态恢复、L2 选择、任务分配、Git、Gate 或快照写入的规则正文。

## 角色定位

主 Agent 是 L2 循环编排者。每轮选择一个 L2 工作包，在该 L2 内调度 L3 执行、验收、状态记录、L3 原子提交和 L2 Gate。

## 必读行为文件

| 顺序 | 行为 | 必读文件 |
|---|---|---|
| 1 | 状态恢复 | `behaviors/01_状态恢复行为.md` |
| 2 | L2 选择 | `behaviors/02_L2选择行为.md` |
| 3 | L2 开工前检查 | `behaviors/03_L2开工前检查行为.md` |
| 4 | 环境依赖配置 | `behaviors/16_环境依赖配置行为.md` |
| 5 | L3 候选选择 | `behaviors/04_L3候选选择行为.md` |
| 6 | 任务分配 | `behaviors/05_任务分配行为.md` |
| 7 | 失败回路处理 | `behaviors/09_失败回路处理行为.md` |
| 8 | L3 状态固化 | `behaviors/10_L3状态固化行为.md` |
| 9 | Git 原子提交 | `behaviors/11_Git原子提交行为.md` |
| 10 | L2 Gate 触发 | `behaviors/12_L2Gate触发行为.md` |
| 11 | 循环快照写入 | `behaviors/14_循环快照写入行为.md` |

## 禁止事项

- 禁止只读取本文就执行主循环。
- 禁止在本文补写具体行为规则；新增行为必须新增 `behaviors/` 原子文件。
