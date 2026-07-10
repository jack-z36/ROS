# L2-03 整体验收卡片：ObservationSnapshot 到 ACT ActionChunk 推理闭环

> [!info] 归属
> - 所属 L2：`l2-03-act-inference`
> - 设计目录：`DOCS/03_工程/阶段四：模型部署/02_implement/l2-03-act-inference_ObservationSnapshot到ACTActionChunk推理闭环/`
> - 验收模式：`direct-local`（Gate 基础环境：CPU + stub policy + recording normalizer）
> - 可选补验：`env-blocked`（真实 policy dry-run，需 L2-01 提供真实 bundle/GPU）
> - 验收轮次上限：3

## 1. 验收目标

证明两件事同时成立：

1. 一次合法同步调用确实完成 `ObservationSnapshot -> ActionChunk`，且输出严格满足 `(chunk_size, 16)`、`float32`、有限值和 16D 物理语义。
2. 实现没有把 L2-01 的资源加载、L2-02 的像素处理、L2-04 的安全、L2-05 的 ROS 输出或 L2-06 的运行调度带入本 L2。

## 2. Required L3 清单

| L3 | 标题 | 验收模式 | Gate 场景 |
|---|---|---|---|
| deploy_021 | ActionChunk 类型定义 | direct-local | S1（类型契约） |
| deploy_022 | Observation 批次准备（一级阶段一） | direct-local | S2（阶段一） |
| deploy_023 | ActionChunk 后处理（一级阶段三） | direct-local | S4（阶段三） |
| deploy_024 | ActInferenceService 与编排入口 | direct-local | S2, S3, S4（三阶段串联） |
| deploy_025 | L2-03 Gate 集成测试与验收脚本 | direct-local | S1-S5（完整闭环与边界） |

## 3. Gate 场景总览

### S1：类型契约

| 场景 | 输入 | 通过现象 | 失败现象 |
|---|---|---|---|
| 合法 ActionChunk | `(N,16)` float32 finite array | 仅保存 actions 的 chunk 被构造 | 缺字段或多运行元数据字段 |
| 非二维输出 | `(16,)` 或 rank 3 array | 抛异常 | 静默接受 |
| 非 16D 输出 | `(N,15)` / `(N,17)` | 抛异常 | 仅检查 rank |
| 非 float32 | float64/int array | 拒绝或在明确转换点统一为 float32 后验证 | 向下游泄漏非 float32 |
| 非有限值 | 含 NaN/Inf | 抛异常 | 替换为零或 clamp |

### S2：阶段一 Observation 批次准备

7 个计算微元独立可验证：兼容性检查、state tensor 化、state normalize、图像绑定、batch 维、batch 组装、device 对齐。

### S3：阶段二 ACT 前向推理

仅调用 `policy.predict_action_chunk(batch)`；不调用 `select_action`；前向失败时异常传播。

### S4：阶段三 ActionChunk 后处理

6 个计算微元独立可验证：raw 结构检查、unbatch、action unnormalize、CPU float32 转换、最终契约检查、ActionChunk 构造。无 clamp/crop/pad/reorder。

### S5：三阶段闭环与边界

三阶段闭环端到端；各阶段失败时链停止；两个 normalizer 调用方向与次数正确；静态边界扫描通过（无 repo loader、无 runtime worker、无 ROS import、无 safety/smoothing 代码、文件只在 types/service/tests）。

## 4. 验收运行目录

```text
仓库根目录
```

## 5. 最低验证层级

`unit` + `import` + `mock`（stub policy + recording normalizer）

## 6. 运行命令

```bash
bash src/model_deploy/act/scripts/l2_03_verify.sh
```

等价于顺序运行全部类型/service/集成/边界测试并汇总。

## 7. 测试输入

- Stub policy（暴露 `predict_action_chunk`，返回可控 sentinel 值；`select_action` 设为失败）
- Recording normalizer（记录 `normalize`/`unnormalize` 调用次数和参数）
- Sentinel snapshot（合法 `ObservationSnapshot` 含 16D state 和模型就绪图像）
- 各类非法输入（错 shape、错 dtype、NaN/Inf、缺相机、空 chunk 等）

## 8. 观察点

| 标签 | 观察内容 | PASS 含义 |
|---|---|---|
| `types.action_chunk_contract` | ActionChunk 字段与方法 | 只存在合法 actions 值对象，无运行元数据 |
| `service.batch.tensorize_state` | state 表达转换 | physical ndarray 正确变为 CPU float32 tensor |
| `service.batch.normalize_state` | state 归一化 | 正确 normalizer 恰好调用一次 |
| `service.batch.bind_images` | 图像绑定 | 相机 key 与 policy feature 精确对应 |
| `service.policy.predict_chunk` | chunk API | 只调用 `policy.predict_action_chunk` |
| `service.output.unnormalize` | action 反归一化 | action normalizer 恰好调用一次 |
| `service.output.no_repair` | 禁止修补 | 未发生 clamp/crop/pad/reorder |
| `service.full_chain` | 三阶段闭环 | 完整 snapshot → ActionChunk |
| `boundary.reuse_only` | 层边界 | config/repo/runtime/ui 无新增产物 |
| `boundary.no_runtime_state` | 运行状态边界 | 无线程、queue、cursor、metrics、fallback |
| `boundary.no_ros_or_hardware` | I/O 边界 | 无 ROS/硬件读写 |

## 9. 通过现象

- `l2_03_verify.sh` 退出码 0
- 终端输出全部 PASS（仅真实 policy 补验可 BLOCKED）
- `service.full_chain`、`service.policy.predict_chunk`、`service.output.no_repair` 和全部 boundary 标签 PASS
- 任何"以默认值、零动作或旧 chunk 替代失败"的结果都不是 PASS

## 10. 失败现象与排查入口

| 失败现象 | 排查入口 |
|---|---|
| types 测试失败 | `tests/types/test_action_chunk.py`，检查 ActionChunk 构造校验逻辑 |
| service 测试失败 | 对应 `tests/service/test_*.py`，检查具体微元实现 |
| 集成测试失败 | `tests/integration/test_l2_03_gate.py`，检查三阶段串联和 stub 配置 |
| 边界测试失败 | 静态扫描源码文件，确认无越界 import 或实现 |
| verify.sh 格式错误 | 对照 `agent_context/04_L2验收机制.md §4.2` 检查输出格式 |

## 11. 未验证项处理方式

| 未验证项 | 处理方式 |
|---|---|
| 真实 ACT policy 前向 | `BLOCKED`：需 L2-01 提供真实 bundle/GPU；不影响本地 Gate 通过 |
| ROS topic 行为 | 不适用：L2-03 无 ROS I/O |
| 硬件命令发送 | 不适用：L2-03 无硬件交互 |
| 真机安全 | 不适用：属于 L2-04/L2-05/L2-06 验收范围 |

## 12. 是否允许进入下游 L2

L2-03 Gate 通过后，允许 L2-06 集成 `ActInferenceService`。

## 13. 是否允许触发 Git 合入

满足以下全部条件才允许合入：

- 全部 5 个 L3 达到可解释状态（PASS_LOCAL 或 DEFER_TO_L2_GATE）
- L2 Gate 通过（本卡片全部场景 PASS，仅真实 policy 补验可 BLOCKED）
- 人类验收签字通过
- 不允许合入：资源加载、fake-policy 生产分支、thread/queue/cursor/metrics、safety/clamp/smoothing 或 ROS/hardware 代码

## 14. 人类验收签字入口

L2-03 Gate 完成后，将人类验收结论写入：

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/验收结果.md
```

格式参见 `agent_context/05_人类验收机制.md §6`。
