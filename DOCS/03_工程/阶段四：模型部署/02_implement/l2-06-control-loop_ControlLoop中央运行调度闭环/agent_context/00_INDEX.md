# L2-06 Agent 上下文入口：ControlLoop 中央运行调度闭环

- `l2_id`：`l2-06-control-loop`
- L2 名称：ControlLoop 中央运行调度闭环
- 人类入口：`../L2架构交互可视化.html`
- Agent 权威入口：本目录 `agent_context/*.md`
- 接口对齐版本：`v2-source-aligned`（2026-07-13）

## 当前权威状态

本版以 `src/model_deploy/act/` 已落地源码的真实 public interface 为事实，修正第一版中把 worker/queue 归给 L2-03、虚构 `SafetyGuard.filter()`、`publish_safe()`、`emit_fallback()`、以及把 `RuntimeMetrics` 误认为上游既有类型等问题。

`agent_context/*.md` 是后续实现、L3 生成和 Gate 的唯一设计权威。根目录 HTML 在当前工作树已有未提交修改，本轮按指定范围没有覆盖；它仍投影旧版接口，状态为 **STALE**，不得用于 L3。HTML 必须在进入 L3 前依据本版 Markdown 单独重新投影，并通过 `HTML_SOURCE_ALIGNMENT`。

## 设计结论速查

| 主题 | 冻结结论 |
|---|---|
| L2-03 接口 | 仅同步 `ActInferenceService.predict_action_chunk(ObservationSnapshot) -> ActionChunk`；异常向调用方传播 |
| 启动资源 | L2-01 repo 唯一提供 frozen `PolicyInputSpec/ActRuntimeResources`；L2-02/03 必须消费同一 spec |
| 异步推理 | `InferenceRequest`、`InferenceResult`、`LatestQueue`、`InferenceWorker` 全部由 L2-06 新增并拥有 |
| ActionChunk | 继续只含 `actions: float32 ndarray[N,16]`；禁止写入 request/time/error/cursor |
| L2-04 接口 | 只调用 `SafetyGuard.filter_action(candidate, previous_safe_action=..., latest_observation=...)` |
| L2-05 接口 | 只构造 `ActionPublishRequest` 并调用 `ActionPublisher.publish(request)`；必须消费 `ActionPublishResult.outcome` |
| permit | L2-06/UI 每 tick 从注入的 `CommandPermitSource` 读取；无来源时默认 deny，真机 Gate 为 BLOCKED |
| fallback | 非 safety 失败不伪造 `SafetyResult`；只写 L2-06 metrics，或在条件满足时重新走真实 safety/publish 链 |
| safe-stop | 逐 tick fail-closed/no-output，可在下一拍恢复；永久 latch 只用于 PARTIAL/FAILED output fault |
| status ownership | `/act/command/status` 只由 L2-05 写；L2-06 只写 `/act/metrics` |
| first-version chunk | active + 单一 pending；cursor 直取；不做 blend、smoothstep、RTC 对齐或跨 chunk 融合 |
| 启动原则 | 所有资源与跨 L2 契约通过后启动 worker，最后创建 timer；任一代码接缝错误是 FAIL，不是 BLOCKED |

## 阅读路由

| 读取目的 | 权威文件 | 重点 |
|---|---|---|
| 确认做什么、不做什么、前置修复 | `01_L2功能边界.md` | 真实输入输出、ownership、启动阻断项 |
| 理解 Pi0.5 参考及不能照搬的部分 | `02_pi05源码3.5层微元拆解.md` | worker/queue、pending chunk、错误信封差异 |
| 获取输入输出、状态机和失败传播 | `03_ACT微元设计与协作.md` | tick、worker、fallback、publish reducer |
| 使用 A/B/C 编号和调用树 | `03a_功能微元总览与组织结构.md` | 唯一编号权威；L3 前必读 |
| 设计自动 Gate | `04_L2验收机制.md` | 真实对象 tracer bullet、PASS/FAIL/BLOCKED |
| 执行人工验收 | `05_人类验收机制.md` | local、ROS dry-run、real-policy、真机阻断 |
| 查看 types 落点 | `06_types层设计.md` | 无新增公共 types；内部记录留在 runtime |
| 查看 config 依赖 | `07_config层设计.md` | 复用字段、启动交叉校验、上游必修项 |
| 查看 repo/资源边界 | `08_repo层设计.md` | policy/normalizer 必须在 timer 前加载并注入 |
| 查看 service 调用 | `09_service层设计.md` | 三个真实 service/public port |
| 查看 runtime 实现蓝图 | `10_runtime层设计.md` | 4 个 runtime 模块、A1-A4、状态与并发 |
| 查看 ROS/CLI/生命周期 | `11_ui层设计.md` | composition root、permit、timer、metrics、shutdown |

## HTML-MD 语义对齐表

> 当前 HTML 为旧版投影。下表给出重新生成 HTML 时必须采用的 Markdown 权威来源。

| HTML view id | HTML view label | Human-visible meaning | Authoritative Markdown | Required Markdown section | Markdown-only detail |
|---|---|---|---|---|---|
| `boundary` | 1 功能边界 | L2-06 消费什么、拥有何种运行责任、向谁输出 | `agent_context/01_L2功能边界.md` | `运行责任与真实接口`、`启动硬前置条件` | 精确签名、outcome reducer、代码级 FAIL |
| `pi05map` | 2 Pi0.5 如何运作 | worker、latest queue、pending chunk、timer 如何协作 | `agent_context/02_pi05源码3.5层微元拆解.md` | `源码证据`、`ACT 复用结论` | Pi0.5 异常丢 result、旧 action metadata 和 blend 污染风险 |
| `blueprint` | 3 开发蓝图 | A/B/C 微元、runtime 调用链和六层落点 | `agent_context/03a_功能微元总览与组织结构.md`; `agent_context/03_ACT微元设计与协作.md`; `agent_context/06_types层设计.md`～`agent_context/11_ui层设计.md` | `编号总表`、`运行时调用树`、各层 `目标源码` | 字段级契约、并发、age、乱序、shutdown |
| `acceptance` | 4 人类验收标准 | 自动 Gate、人工步骤、FAIL 定位和硬件 BLOCKED | `agent_context/04_L2验收机制.md`; `agent_context/05_人类验收机制.md` | `验证脚本合同`、`人工验收项` | 完整标签映射、pytest node、签字记录 |

## 后续 Agent 加载顺序

1. 读取 `01_L2功能边界.md`，确认跨 L2 前置修复没有被跳过。
2. 读取 `03a_功能微元总览与组织结构.md`，冻结 A/B/C 编号。
3. 读取 `03_ACT微元设计与协作.md` 与对应六层文件。
4. 读取 `04_L2验收机制.md`，先写真实接缝测试，再写实现。
5. 不得从旧 HTML、旧 dispatch、Contract Delta 或 Pi0.5 类型字段反推当前接口。

## 当前就绪度

- Markdown 接口设计：v2 source-aligned 已完成并通过结构 validator，可作为修订权威。
- 直接生成 L2-06 L3：**否**。必须先通过 `01_L2功能边界.md` 的代码级前置 Gate，并由用户确认本版微元/状态机。
- HTML 投影：**STALE**，进入 L3 前必须同步。
- 真机：permit source、driver safe-stop、E-stop、硬件授权未确认，保持 `BLOCKED_HARDWARE`。

## 污染检查

以下内容只能作为负向检查或只读参考，不能覆盖本版边界：

- 旧 layer-based L2 id；
- 独立 `l2-04-action-smoothing`、smoothstep、blend、RTC 对齐；
- `Contract Delta`；
- 阶段二模板；
- Pi0.5 的 14D/26D action/state、`ControlCommand.accepted`、直接硬件 publish；
- 第一版 L2-06 文档中的 `L2-03 worker/queue`、`SafetyGuard.filter`、`publish_safe`、`emit_fallback`。
