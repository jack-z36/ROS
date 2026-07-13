# L2-05 整体验收卡片：单步 Action 到执行器 Topic 适配发送闭环

> [!info] 归属
> - 所属 L2：`l2-05-action-publisher`
> - 设计权威：目标 L2 `agent_context/*.md`；用户明确指定 HTML 不是 L3/Gate 来源。
> - 主验收模式：`direct-local`（Python + fake publisher）
> - 补验模式：`env-blocked`（ROS 观察）、`hardware-blocked`（真机）
> - 验收轮次上限：3

## 1. 验收目标

同时证明：

1. C1-C21、B1-B3 与 A1 按权威调用树落地，L2-06 只需同步调用 B3。
2. safe 16D TCP action 能变成候选 payload/消息，只有“显式 CLI enable AND CommandPermit.allowed”才允许四路 command。
3. policy/status 观察、partial 失败事实、deadband 状态和 RAM result 可验证；ROS publish 不被伪称为硬件到位。
4. 实现无 L2-05 runtime/repo 产物，无 mode/accepted/bridge/mux/TF/IK/SDK 污染。

## 2. Required L3 清单

| L3 | 标题 | 主验收 | Gate 场景 |
|---|---|---|---|
| deploy_041 | Action 发布类型与输出配置契约 | direct-local | G01-G03 |
| deploy_042 | Topic 候选载荷生成 | direct-local | G04-G06 |
| deploy_043 | ROS 候选消息打包 | direct-local | G07-G08 |
| deploy_044 | ActionPublisher 门控发布闭环 | direct-local | G09-G17 |
| deploy_045 | L2 Gate 集成测试与验收脚本 | direct-local + blocked supplements | G01-G19 |

## 3. Gate 场景分组

| 分组 | 场景 | PASS 含义 |
|---|---|---|
| types/config | G01-G03 | 冻结契约、CLI default-off、显式开启可审计 |
| service B1 | G04-G06 | PASS/ADJUSTED -> C4，分段/frame/夹爪映射正确 |
| ui B2 | G07-G08 | 五消息先完整构造，不含 status/副作用 |
| ui B3 | G09-G15 | 双门控、调用顺序、partial、deadband、status/result 真实 |
| boundary/mock | G16-G17 | 无越界，多 tick 同步返回可供 L2-06 消费 |
| ROS/hardware | G18-G19 | 环境可用则补验；否则以完整理由 BLOCKED |

## 4. 运行命令

```bash
bash src/model_deploy/act/scripts/l2_05_verify.sh --case local
```

人类分项验收使用 `agent_context/05_人类验收机制.md` 中 H01-H09；默认不执行真机。

## 5. 通过现象

- verify 退出码 0；G01-G17 无 FAIL、required 无 BLOCKED。
- CLI 缺省关闭与 permit=False 时四路 command 调用数恒为 0。
- 允许时的完整/部分写出都在 C6/status 中如实反映。
- G18/G19 若未执行，显示对应 BLOCKED 原因，不写 PASS。

## 6. 失败排查

| 失败 | 入口 |
|---|---|
| types/config | deploy_041 + `test_action_publish.py` / `test_command_output_config.py` |
| B1 payload | deploy_042 + `test_action_output_adapter.py` |
| B2 message | deploy_043 + `test_action_publisher_messages.py` |
| B3 gate/partial/state | deploy_044 + `test_action_publisher.py` |
| Gate/format/boundary | deploy_045 + `test_l2_05_gate.py` / `l2_05_verify.sh` |

## 7. 未验证项与下游放行

- L2-06 真实 CLI parser、CommandPermit 汇总、fallback/retry 是 `downstream-l2`。
- 无 ROS 时 G18=`BLOCKED_ENV`；无真机/授权/急停时 G19=`BLOCKED_HARDWARE_EXPECTED`。
- `hardware-blocked` 不能写成真机通过。
- G01-G17 全 PASS 后可交给 L2-06 进行 RAM 接口集成；Git 合入仍需人类验收签字与风险记录。

## 8. 人类验收签字入口

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/验收结果.md
```

