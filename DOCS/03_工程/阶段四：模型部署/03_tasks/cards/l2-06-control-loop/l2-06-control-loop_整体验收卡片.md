# L2-06 整体验收卡片：ControlLoop 中央运行调度闭环

> [!info] 归属
> - 所属 L2：l2-06-control-loop
> - 设计权威：目标 L2 agent_context/*.md；HTML 不是 L3/Gate 生成来源。
> - 主验收模式：direct-local（真实 production contracts + fake external boundaries）。
> - 补验模式：env-blocked、hardware-blocked。
> - 验收轮次上限：3。
> - 当前调度状态：blocked；deploy_051/052 已冻结执行，deploy_056～060 负责闭合 P0 owner seam，deploy_053～055 等待全部依赖。

## 1. 验收目标

同时证明：

1. A1-A5、B1-B12、C1-C26 按唯一编号树落地，L2-03 仍是同步 service，全部 queue/worker/cursor/fallback/metrics 归 L2-06。
2. control timer 永不等待 policy；最多一个 outstanding；active/pending/cursor、age、fallback与结果关联确定可测。
3. 每个 candidate 真实经过 L2-04 与 L2-05，六种 outcome/provenance/echo归约正确，任何 fault fail-closed。
4. production startup 原子，worker/timer顺序正确，shutdown有界；/act/command/status单 writer，L2-06只写/act/metrics。
5. local、ROS dry-run、real-policy和real-command结论分离；BLOCKED不伪装PASS。
6. L1 与 L2-01～06 的人类 HTML、Agent agent_context 和最终源码不存在 ownership、签名或数据合同双轨。

## 2. Required L3 清单

| L3 | 标题 | 主验收 | Gate 场景 | 当前状态 |
|---|---|---|---|---|
| deploy_051 | 推理通道与运行指标基础 | direct-local | G04 | blocked |
| deploy_052 | InferenceWorker 串行异步执行 | direct-local | G05 | blocked |
| deploy_053 | ControlLoop 中央调度状态机 | direct-local | G06-G07 | blocked |
| deploy_054 | ActDeployNode 原子装配与生命周期 | direct-local + blocked supplements | G08 | blocked |
| deploy_055 | L2 Gate 跨模块集成与验收脚本 | direct-local + blocked supplements | G01-G12 | blocked |
| deploy_056 | L2-01 启动资源与配置接缝修复 | direct-local | G02-G03 | blocked |
| deploy_057 | L2-02 观测流水线契约修复 | direct-local + env supplement | G03 | blocked |
| deploy_058 | L2-03 Canonical Spec 消费接缝 | direct-local | G03 | blocked |
| deploy_059 | L2-04 安全端口与设计投影对齐 | static-review + local tests | G03/G07 | blocked |
| deploy_060 | L2-05 发布失败追因契约 | direct-local | G03/G07 | blocked |

## 3. Owner 修复任务与放行关系

| L3 | owner | 必须证据 |
|---|---|---|
| deploy_056 | L2-01 | default config、CLI flag、PolicyInputSpec/ActRuntimeResources/loader、L1/L2-01 HTML-agent_context-source 对齐 |
| deploy_057 | L2-02 | typed ObservationPipeline、camera/image/gripper、owned snapshot、monotonic freshness、L2-02 双投影对齐 |
| deploy_058 | L2-03 | service 消费并公开同一个 canonical PolicyInputSpec、同步 service-only、L2-03 双投影对齐 |
| deploy_059 | L2-04 | exact safety signature、三状态、无 accepted 双轨、L2-04 双投影对齐 |
| deploy_060 | L2-05 | invalid-input 稳定异常、failure_stage/failed_topic/reason provenance、L2-05 双投影对齐 |
| deploy_055 | L2-06 | L2-06 HTML/agent_context 按最终源码同步且完整 Gate PASS |

这些任务是用户明确授权的 L2-06 集成修复例外，但实现和文档语义仍归原 owner L2。deploy_051/052 完成前 056～060 保持 blocked；056 完成后才放行 057/058；全部 owner 任务 PASS_LOCAL 后才放行 053。

## 4. Gate 场景分组

| 场景 | 分组 | PASS 含义 |
|---|---|---|
| G01 | types/boundary | ActionChunk纯净、无ControlDecision、public imports additive |
| G02 | config/repo | default config、static CLI、canonical resources/spec和cross-contract |
| G03 | observation/service/publish seam | 实产snapshot→service、真实Safety/Publisher接口和provenance |
| G04 | channel/metrics | envelope、capacity-one close、immutable metrics |
| G05 | worker | nonblocking、serial、error recovery、stop/join |
| G06 | scheduling | correlation、active/pending、prefetch/horizon、age/copy |
| G07 | fallback/output | B6/B8、六outcome、deferred reason、fault latches |
| G08 | UI/lifecycle | preflight、atomic startup、entrypoint、permit/metrics/shutdown |
| G09 | local full Gate | required production contracts、baseline、HTML alignment均0 FAIL |
| G10 | ROS dry-run | policy/status/metrics可见，四路command=0，有界退出 |
| G11 | real-policy dry-run | real bundle/GPU合法chunk，command=0 |
| G12 | real command | 仅在permit/E-stop/driver/授权齐备后人工受控验证 |

## 5. 运行命令

```bash
bash src/model_deploy/act/scripts/l2_06_verify.sh \
  --scope local --policy fake \
  --config src/model_deploy/act/tests/fixtures/l2_06_fake.yaml
```

外部补验按目标 L2 agent_context/05_人类验收机制.md 执行。默认不运行真实 command。

## 6. 通过现象

- local verify退出0，G01-G09与baseline为0 FAIL；required local项无BLOCKED。
- 慢/错policy不阻塞tick，in-flight可终结，chunk与fallback不使用过期源。
- Safety/Publisher调用次数与六outcome矩阵一致；PARTIAL/FAILED或runtime invariant后command=0。
- ROS dry-run若可运行，outcome=OBSERVED、policy/status/metrics可见、四command严格0。
- G10-G12未执行时只记录精确外部BLOCKED，不写PASS。

## 7. 失败排查

| 失败分组 | 入口 |
|---|---|
| channel/metrics | deploy_051 + test_inference_channel.py / test_runtime_metrics.py |
| worker | deploy_052 + test_inference_worker.py |
| ControlLoop | deploy_053 + test_control_loop.py |
| startup/UI | deploy_054 + test_startup_preflight.py / test_act_deploy_node.py / test_act_deploy_main.py |
| cross-L2/verify | deploy_055 + 三条real-chain tests / test_l2_06_gate.py / l2_06_verify.sh |
| L2-01 config/resources | deploy_056；不得由 UI 私下加载或重建 spec |
| L2-02 observation | deploy_057；不得由 ControlLoop 临时转置/猜 camera |
| L2-03 spec consumer | deploy_058；不得把 worker/queue 迁回 service |
| L2-04 safety port | deploy_059；不得添加 accepted 兼容 |
| L2-05 provenance | deploy_060；不得由 L2-06 从 outcome 猜 stage/topic |

## 8. 未验证项与放行

- deploy_051/052 正在按用户安排执行且冻结；其任务、卡片和 dispatch 条目不得由本次重排改动。
- deploy_056～060 与 deploy_053～055 当前仍 blocked，必须按七个 wave 放行。
- ROS、bundle/GPU、permit topology、driver/E-stop、硬件和操作者授权分别判定，不互相代替。
- hardware-blocked 不能写成真机通过。
- local Gate通过后才进入人类验收；Git合入仍需人类签字与风险记录。

## 9. 人类验收签字入口

DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-06-control-loop/验收结果.md
