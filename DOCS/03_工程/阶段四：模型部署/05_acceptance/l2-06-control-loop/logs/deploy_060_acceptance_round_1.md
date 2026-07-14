# 验收反馈：deploy_060 L2-05 发布失败追因契约

- 验收模式：`direct-local`（进程内 FakeNode，未连接 driver/ROS/硬件）
- 验收轮次：1
- 验收日期：2026-07-13
- 验收 Agent：只读 sub-agent；未编辑任何源码 / 测试 / dispatch / 卡片 / Git 状态

## 结论

**PASS_LOCAL**

所有 PASS_LOCAL 清单项满足，L3 指定测试集 129 passed，act 全量回归 743 passed / 1 skipped（与本 L3 无关，无新增失败），静态负向检查干净。建议主 Agent 在归档前先做范围核对（见“非阻塞注意”）。

## 检查清单（卡片 §3 PASS_LOCAL）

| # | 清单项 | 结果 | 依据 |
|---|---|---|---|
| 1 | invalid input 不再触发 `__r` AttributeError，异常类型/消息稳定 | ✅ PASS | 静态检查：两文件无 `type(x).__r`；运行期非法输入稳定抛 `TypeError`/`ValueError`（见命令/输出）。 |
| 2 | ActionPublishResult 六 outcome invariant 不可违反 | ✅ PASS | `action_publish.py:392-466` `__post_init__` 矩阵逐 outcome 强制 stage/topic/reason；`TestPublishProvenance` 红/绿全过。 |
| 3 | policy/status/四路 command 每故障点精确 provenance，无后续 command 泄漏 | ✅ PASS | `action_publisher.py` B3 各分支写入精确 stage/topic；command 循环 `break`；`test_policy_publish_failure_provenance`/`test_command_partial_provenance` 验证无泄漏。 |
| 4 | request echo、startup switch、permit echo 完整 | ✅ PASS | `_build_publish_result` 透传 `action_id`/`command_output_enabled`(C7)/`command_permitted`(permit)；status JSON 含全部字段。 |
| 5 | `/act/command/status` 仍 L2-05 单 writer；status failure 不伪造 result | ✅ PASS | 仅 1 个 `status` publisher；`_publish_status_best_effort` 失败仅置 `status_published=False`，不改 outcome/stage；`test_status_failure_does_not_fake_result` 通过。 |
| 6 | L2-05 HTML 与 agent_context 同步 | ⚠️ 部分（非阻塞） | 权威 `agent_context/06_types层设计.md` 与 `11_ui层设计.md` 已同步六 outcome 矩阵、单 writer、失败不伪造（见下）。HTML C6 表其余字段 `safety_ok`/`sent_to_driver`/`failure_reason` 为历史快照，与真实代码不符；本 L3 仅追加 `failure_stage`/`failed_topic`（见“非阻塞注意”）。 |

## 必跑命令与输出

### 1) L3 指定验证集（卡片 §2 / 任务 §9）

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/types/test_action_publish.py \
  src/model_deploy/act/tests/ui/test_action_publisher_messages.py \
  src/model_deploy/act/tests/ui/test_action_publisher.py \
  src/model_deploy/act/tests/integration/test_l2_05_gate.py -q
```

结果：**129 passed in 0.15s**（exit 0）。所有 4 文件存在且全部通过，无 missing file。

### 2) 广度回归

```bash
PYTHONPATH=src python3 -m pytest src/model_deploy/act/tests -q
```

结果：**743 passed, 1 skipped, 2 warnings in 3.48s**（exit 0）。
- 2 warnings 来自 `tests/runtime/test_inference_worker.py`（KeyboardInterrupt 线程告警），与 deploy_060 无关。
- 与本 L3 实施前基线一致，无由本任务引入的新失败。

### 3) 静态负向检查（卡片 RUN 段）

```bash
grep -rn "type(x).__r\|reason_code=None" \
  src/model_deploy/act/types/action_publish.py \
  src/model_deploy/act/ui/action_publisher.py
```

结果：
- `type(x).__r` → **无匹配**：执行 agent 所述 4× `type(x).__r` → `type(x)!r` 已修复确认。
- `reason_code=None` → 唯一命中 `action_publish.py:97`：
  `"CommandPermit with allowed=True must have reason_code=None"` —— 这是 `CommandPermit.__post_init__` 的 **ValueError 用户提示字符串**，非代码赋值，不属于 `__r` 类 bug，属良性命中。

### 4) 六 outcome 不变量复核（人工走查 `__post_init__`）

| outcome | reason_code | failure_stage | failed_topic | 代码位置校验 |
|---|---|---|---|---|
| REJECTED | 非空（SAFETY_REJECTED） | 必须 `"safety"` | 必须 None | ✅ `:414-423` |
| OBSERVED/BLOCKED | permit reason / None | 必须 None | 必须 None | ✅ `:424-438` |
| PUBLISHED | None | 必须 None | 必须 None | ✅ `:424-438` |
| FAILED | 非空 | 必须非 None；I/O stage 强制 topic | policy_publish/command_publish 必带 topic，command_build 必 None | ✅ `:439-455` |
| PARTIAL | 非空（COMMAND_PUBLISH_IO_ERROR） | 必须 `"command_publish"` | 必带精确 topic | ✅ `:456-466` |

Publisher 侧各分支（B1 安全/契约、B2 消息、C17 policy、command 循环、status best-effort）均向 `_build_publish_result`/`_finalize` 透传一致 stage/topic；command 循环在 `ActionPublishIoError` 时 `break`，无后续 command 泄漏。

## 非阻塞注意（不触发 FAIL_LOCAL）

1. **HTML C6 表历史 stale 字段**：`L2架构交互可视化.html` 第 853/857/858 行仍为 `safety_ok` / `sent_to_driver` / `failure_reason`，与真实代码字段（`command_output_enabled` / `command_permitted` / `outcome` / `status_published` / `reason_code`）不一致。本 L3 仅在第 859/860 行追加了 `failure_stage` / `failed_topic`。该 stale 为 PRE-EXISTING（执行 agent §18.4 已声明），超出 deploy_060 外科手术边界。
   - 建议：另起一个 design-package L3 全面刷新 L2-05 HTML C6 表，不在本 L3 范围内补做。
   - 卡片明确：不因此项单独 FAIL_LOCAL。

2. **工作树含 sibling L3 的未提交改动**：`git status` 显示除 deploy_060 范围内文件外，还存在 `config/schema.py`、`config_files/deploy.yaml`、`repo/*`、`runtime/*`、l2-01/l2-04/l2-06 的 `agent_context/*` 等多处未提交改动。这些属于同 wave（l2-06-control-loop-p3）**其他 L3 任务**（如 runtime/reducer/config 类任务）的产物，不在 deploy_060 的 `conflict_scope` 内。
   - deploy_060 自身 §18.1 变更表仅列：4 个源文件 + 4 个测试文件 + L2-05 `06_types`/`11_ui` agent_context + L2-05 HTML，均在允许范围内。
   - 建议主 Agent 归档前按 dispatch `conflict_scope` 逐任务隔离确认；这不影响 deploy_060 本卡 PASS_LOCAL 判定。

## 修复请求（Fix Requests）

无。所有必跑测试通过，静态检查干净，六 outcome 不变量与单 writer/失败不伪造契约均满足。无需执行 agent 返工。

## 对主 Agent 的归档提示

本卡结论为 **PASS_LOCAL**。依据 `skills/stage4-l3-orchestrator/SKILL.md` §65-82 的 PASS_LOCAL Archive Rule，**主 Agent 必须将 L3 任务文件从：**

```
DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_060_L2-05发布失败追因契约.md
```

**归档至：**

```
DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-06-control-loop/deploy_060_L2-05发布失败追因契约.md
```

该归档动作由主 Agent 完成，验收 sub-agent 不执行。归档前建议先处理上述“非阻塞注意 #2”的范围隔离核对。归档解除 deploy_060 对 deploy_053/054/055 的 `blocks` 阻塞（卡片 §4），使 L2-06 C19 reducer 所需的六 outcome provenance 事实可用。

## 横向贡献（卡片 §4 L2 Gate）

- 贡献场景 G03/G07；交付 P0-10（稳定非法输入异常 + publish failure provenance）。
- 为 L2-06 C19 reducer 提供可机械归约的 `failure_stage` / `failed_topic` 事实，L2-06 仅保存并核验 L2-05 返回值即可 fail-closed，无需从 outcome 反推失败位置。
- 完成后解阻塞 deploy_053/054/055。
