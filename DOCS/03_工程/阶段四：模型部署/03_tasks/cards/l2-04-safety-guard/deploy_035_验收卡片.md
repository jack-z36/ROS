# 验收卡片：deploy_035 L2-04 Gate 集成测试与验收脚本

> [!info] 归属
> - 所属 L2：`l2-04-safety-guard`
> - 对应 L3：`deploy_035`
> - 验收模式：`direct-local`
> - 辅助验收模式：`static-review`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_035` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_035_L2Gate集成测试与验收脚本.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/tests/integration/test_l2_04_gate.py`、`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh`、执行摘要、verify 终端输出 |
| 前置条件 | deploy_031~034 均已完成并通过验收 |

## 2. 验收模式

`direct-local` + `static-review`：运行集成测试和验收脚本，同时静态扫描边界。

## 3. 必跑命令

```bash
bash "DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh"
```

如果命令无法运行，必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `test_l2_04_gate.py` 存在于 `src/model_deploy/act/tests/integration/test_l2_04_gate.py`。
- [ ] `l2_04_verify.sh` 存在于 `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh`。
- [ ] 覆盖 `04_L2验收机制.md` §3 全部核心标签：
  - [ ] TYPES-RESULT
  - [ ] INPUT-SHAPE / INPUT-FINITE / QUAT-CANDIDATE
  - [ ] REFERENCE-ORDER / REFERENCE-BOOTSTRAP / REFERENCE-MISSING
  - [ ] POSE-TRANSLATION / POSE-ROTATION
  - [ ] GRIPPER-RANGE / GRIPPER-STEP
  - [ ] BIMANUAL-ASSEMBLY / OUTPUT-INVARIANT / RESULT-STATUS
  - [ ] PURITY-IMPORT
- [ ] verify 输出含分层标签行与 `SUMMARY: N PASS / N FAIL / N BLOCKED`。
- [ ] verify 退出码 0；无 FAIL；核心标签不得 BLOCKED。
- [ ] 不依赖 ROS/hardware 才能跑核心 Gate。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未把生产算法“顺手大改”到超出 Gate 任务范围（允许最小 bugfix，但必须在摘要声明）。

### FAIL_LOCAL 条件（任一命中）

- 任一核心标签 FAIL。
- verify 退出码非 0。
- 用 BLOCKED 伪装核心标签 PASS。
- 依赖真机/ROS 才能通过核心 Gate。
- 验收脚本路径与任务声明不符。

### BLOCKED_ENV

- 缺少 Python3、pytest、bash 或 numpy，无法运行 verify。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 对应 Gate 场景 | S1-S5 全量 |
| 场景覆盖 | mock Gate 一键验证与边界纯度 |
| L2 Gate 依赖本 L3 | 是。本 L3 即 Gate 可执行入口 |
| 未完成影响 | 不能宣称 L2-04 mock Gate 通过，不得放行 L2-05/L2-06 集成设计 |
