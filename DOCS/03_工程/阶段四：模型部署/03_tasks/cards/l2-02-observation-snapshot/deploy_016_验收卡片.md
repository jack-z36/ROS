# 验收卡片：deploy_016 L2 Gate 集成测试与验收脚本

> [!info] 归属
> - 所属 L2：`l2-02-observation-snapshot`
> - L3 编号：`deploy_016`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_016` |
| 验收模式 | `direct-local` |
## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_016_L2Gate集成测试与验收脚本.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/tests/integration/test_l2_02_gate.py`、`src/model_deploy/act/scripts/l2_02_verify.sh`、执行摘要、pytest 输出、bash 脚本输出 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 pytest 集成测试和 bash 验收脚本。

## 3. 必跑命令

```bash
# 集成测试
python3 -m pytest src/model_deploy/act/tests/integration/test_l2_02_gate.py -v

# 统一验收脚本
bash src/model_deploy/act/scripts/l2_02_verify.sh
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `test_l2_02_gate.py` 存在于 `src/model_deploy/act/tests/integration/test_l2_02_gate.py`。
- [ ] `l2_02_verify.sh` 存在于 `src/model_deploy/act/scripts/l2_02_verify.sh`。
- [ ] 集成测试覆盖：test_full_mock_pipeline、test_missing_field_pipeline、test_stale_pipeline、test_boundary_no_overreach、test_import_without_ros、test_boundary_no_config_repo。
- [ ] 全字段 mock pipeline 端到端通过：collector → snapshot → buffer → latest_observation → encoded_state.shape == (16,)。
- [ ] 缺字段 pipeline：snapshot 返回 None，missing_fields 包含字段名，buffer 不被写入。
- [ ] 过期 pipeline：snapshot(max_age_s) 返回 None，stale_fields 非空。
- [ ] 边界不越界：rg 扫描 service/runtime/ui 无 `predict_action_chunk|ActionChunk|SafetyGuard|publish.*hardware|driver` 实现。
- [ ] config/repo 目录无 L2-02 新增 .py 文件。
- [ ] 无 ROS 环境下全模块栈 import 不失败。
- [ ] l2_02_verify.sh 按分层分组输出（types/service/runtime/ui/边界）。
- [ ] 每标签一行 `PASS|FAIL|BLOCKED` + 标签名 + 说明。
- [ ] FAIL 附文件、微元、pytest 节点、错误摘要（缩进 `├─/└─`）。
- [ ] 末行汇总 `N PASS / N FAIL / N BLOCKED`。
- [ ] 退出码：全部 PASS → 0；任一 FAIL → 1。
- [ ] 12 个验证标签全部覆盖：contract.encoded_state_dim、contract.importable、collector.mock_snapshot、collector.missing_reject、collector.stale_reject、preprocess.image、buffer.latest_only、buffer.max_age、adapter.no_ros_importable、boundary.no_overreach、boundary.no_config_repo、adapter.real_subscription (BLOCKED_ENV)。
- [ ] pytest 全部通过，无 skip。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未修改 types/、service/、runtime/、ui/ 或 pi05/。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- 集成测试未覆盖全部 6 个 L2 Gate 场景。
- 验收脚本未覆盖全部 12 个验证标签。
- 验收脚本输出格式不符合 `04_L2验收机制.md §4` 规约。
- 退出码不正确（全部 PASS 时退出码非 0）。
- 修改了禁止修改的文件。
- pytest 失败或有未解释的 skip。

### BLOCKED_ENV

- 缺少 Python3、pytest、bash 或 rg/find，无法运行测试或验收脚本。
- adapter.real_subscription 标签因无 ROS 环境标记 BLOCKED_ENV（可解释，不判 FAIL）。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 影响 L2 Gate | 是（L2-02 的 Gate 关闭 L3） |
| 对应场景 | S1 Mock 全字段 snapshot 组装、S2 缺字段/过期拒绝、S3 图像预处理、S4 Latest-only buffer 语义、S5 无 ROS 可 import、S6 边界不越界 |
| 贡献 | 端到端 mock 全链路验证 + 统一验收脚本，覆盖全部 12 个 L2 Gate 标签，是 L2-02 的 Gate 总验收入口 |
| 仍需后续 L3 | 无（本 L3 是 L2-02 的最后一个 L3） |

## 6. 验收结论写入位置

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs/deploy_016_acceptance_round_<n>.md
```

结论格式：

```text
结论：PASS_LOCAL / FAIL_LOCAL / BLOCKED_ENV / DEFER_TO_L2_GATE
检查项逐条结果：
- ...
l2_02_verify.sh 汇总输出：
- N PASS / N FAIL / N BLOCKED
blocked 项说明：
- adapter.real_subscription: 当前无 ROS 环境，真实 topic 订阅验收 BLOCKED_ENV
反馈说明：
```
