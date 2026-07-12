# 验收卡片：deploy_034 SafetyGuard 编排与入口

> [!info] 归属
> - 所属 L2：`l2-04-safety-guard`
> - 对应 L3：`deploy_034`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_034` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_034_SafetyGuard编排与入口.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/service/safety_guard.py`、`src/model_deploy/act/service/__init__.py`、`src/model_deploy/act/tests/service/test_safety_guard.py`、执行摘要、pytest 输出 |
| 前置条件 | deploy_031、deploy_032、deploy_033 已完成 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 service 编排测试。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_safety_guard.py src/model_deploy/act/tests/service/test_safety_primitives.py -v
```

如果命令无法运行，必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] 存在 `SafetyGuard` class，构造注入 immutable SafetyConfig。
- [ ] 对外入口 `filter_action(candidate, previous_safe_action=None, latest_observation=None) -> SafetyResult`。
- [ ] 实现 B1-B5 编排（可为私有方法），调用树符合 `03a`。
- [ ] RESULT-STATUS：合法小步 → PASS；可投影超限 → ADJUSTED 且 action 非 None、findings 非空；契约/无基准失败 → REJECTED 且 action is None。
- [ ] 连续两次调用时，Guard 不隐式记忆 previous（无状态性）。
- [ ] 不实现 fallback/hold/safe-stop。
- [ ] 不 import runtime/ui/ROS/hardware。
- [ ] 既有 primitives 测试仍 PASS。
- [ ] pytest 全部通过，无 skip。
- [ ] 产物路径与 L3 声明一致。

### FAIL_LOCAL 条件（任一命中）

- ADJUSTED 被标成 REJECTED/PASS。
- REJECTED 仍返回可发布 action。
- Guard 保存 previous_safe_action 或 metrics 跨调用状态。
- 对 previous 与 observation 双重裁剪。
- pytest 失败。

### BLOCKED_ENV

- 缺少 Python3、pytest 或 numpy。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 对应 Gate 场景 | S4 service orchestration |
| 场景覆盖 | L2-06 可调用的完整入口与三态结果 |
| L2 Gate 依赖本 L3 | 是 |
| 未完成影响 | deploy_035 无法跑端到端 mock Gate |
