# 验收卡片：deploy_025 L2-03 Gate 集成测试与验收脚本

> [!info] 归属
> - 所属 L2：`l2-03-act-inference`
> - 对应 L3：`deploy_025`
> - 验收模式：`direct-local`
> - 辅助验收模式：`static-review`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_025` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-act-inference/deploy_025_Gate集成测试与验收脚本.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-act-inference/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/tests/integration/test_l2_03_gate.py`、`src/model_deploy/act/scripts/l2_03_verify.sh`、执行摘要、verify.sh 终端输出 |
| 前置条件 | deploy_021~004 均已完成并通过验收 |

## 2. 验收模式

`direct-local` + `static-review`：运行集成测试和验收脚本，同时静态扫描边界。

## 3. 必跑命令

```bash
bash src/model_deploy/act/scripts/l2_03_verify.sh
```

等价于顺序运行全部类型/service/集成/边界测试并汇总。如果命令无法运行，必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `test_l2_03_gate.py` 存在于 `src/model_deploy/act/tests/integration/test_l2_03_gate.py`。
- [ ] `l2_03_verify.sh` 存在于 `src/model_deploy/act/scripts/l2_03_verify.sh`。
- [ ] 集成测试覆盖全部 Gate 场景：
  - [ ] `service.full_chain`：合法 snapshot + recording normalizer + deterministic stub policy → 返回只含 actions 的 `ActionChunk`；两个 normalizer 各调用一次。
  - [ ] `service.error_stops_chain`：阶段一/二/三分别失败时，后续阶段不执行，无部分输出。
  - [ ] `service.policy.predict_chunk`：只调用 `predict_action_chunk`，不调用 `select_action`。
  - [ ] `service.output.no_repair`：超范围 sentinel、过长/过短 raw 不被 clamp/crop/pad；段序不重排。
  - [ ] `boundary.no_resource_io`：静态扫描 service/types 无 bundle/checkpoint/path/json/yaml loader 调用。
  - [ ] `boundary.no_runtime_state`：静态扫描 service/types 无 Thread/queue/timer/request/cursor/metrics/fallback。
  - [ ] `boundary.no_ros_or_hardware`：静态扫描 service/types 无 ROS import、publisher/subscriber、SDK/Modbus/serial。
  - [ ] `boundary.no_safety_or_smoothing`：静态扫描 service/types 无 clamp、delta/IK/collision、安全检查、blend/smooth/RTC。
  - [ ] `boundary.only_allowed_layers`：文件列表检查，L2-03 新增实现只在 `types/`、`service/`、tests。
- [ ] verify.sh 终端输出格式符合 `agent_context/04_L2验收机制.md §4.2`：
  - [ ] 分层输出（`[ types ]`、`[ config / repo ]`、`[ service ]`、`[ runtime / ui / boundary ]`）。
  - [ ] 每行格式 `PASS|FAIL  <label>  <description>`。
  - [ ] FAIL 行紧随定位块（文件、class、微元、pytest、摘要）。
  - [ ] 末尾汇总 `N PASS / N FAIL / N BLOCKED`。
- [ ] verify.sh 退出码为 0（全部必须项 PASS，仅真实 policy 补验可 BLOCKED）。
- [ ] 无 FAIL 标签。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未修改 deploy_021~004 的产物文件。
- [ ] 未修改 `src/model_deploy/pi05/`、其他层文件或 dispatch。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- 任一必须项 FAIL（`service.full_chain`、`service.policy.predict_chunk`、`service.output.no_repair`、全部 boundary 标签）。
- verify.sh 退出码非 0（排除仅真实 policy 补验 BLOCKED）。
- 集成测试依赖真实 bundle、GPU 或 ROS。
- 静态边界扫描使用不可靠的匹配模式（如只检查 import 语句但忽略动态调用）。
- 修改了 deploy_021~004 的产物文件。

### BLOCKED_ENV

- 缺少 Python3、pytest、torch 或 bash，无法运行 verify.sh。
- 真实 policy 补验因缺 bundle/GPU 而无法运行（标记 `BLOCKED` 可接受，不影响本地 Gate 通过）。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 对应 Gate 场景 | S1（类型契约）、S2（阶段一）、S3（阶段二）、S4（阶段三）、S5（三阶段闭环与边界） |
| 场景覆盖 | 完整 L2-03 Gate 验收：三阶段闭环 + 静态边界扫描 + 标准化验收脚本 |
| L2 Gate 依赖本 L3 | 是。本 L3 是 l2-03-act-inference 的最后一个 L3，汇总全部 Gate 场景 |
| 未完成影响 | L2 Gate 缺少标准化验收证据，无法进入人类验收和合入流程 |

## 6. L2 Gate 放行条件（汇总）

本 L3 通过后，L2-03 Gate 的全部 required L3（deploy_021~005）即达到可解释状态。以下条件全部满足才允许 L2-06 集成该 service：

- 三个一级阶段和总入口的单测全部 PASS。
- strict raw/final shape 测试 PASS。
- 两个 normalizer 的调用方向与调用次数测试 PASS。
- `select_action` 未被调用。
- `ActionChunk` 无运行元数据。
- 静态边界测试 PASS。
- 不允许合入：资源加载、fake-policy 生产分支、thread/queue/cursor/metrics、safety/clamp/smoothing 或 ROS/hardware 代码。
