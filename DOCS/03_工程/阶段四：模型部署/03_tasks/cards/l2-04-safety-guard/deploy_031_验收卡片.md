# 验收卡片：deploy_031 SafetyResult 类型定义

> [!info] 归属
> - 所属 L2：`l2-04-safety-guard`
> - 对应 L3：`deploy_031`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_031` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_031_SafetyResult类型定义.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/types/safety_result.py`、`src/model_deploy/act/types/__init__.py`、`src/model_deploy/act/tests/types/test_safety_result.py`、执行摘要、pytest 输出 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 unit / import 测试。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_safety_result.py -v
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `safety_result.py` 存在于 `src/model_deploy/act/types/safety_result.py`。
- [ ] 存在 `SafetyStatus`（PASS/ADJUSTED/REJECTED）、`SafetyCode`、`SafetyFinding`、`SafetyResult`。
- [ ] `SafetyFinding` 与 `SafetyResult` 为 frozen dataclass。
- [ ] `REJECTED` 时 `action is None`；PASS/ADJUSTED 时 `action` 非 None。
- [ ] 非法 status/action 组合在构造时拒绝。
- [ ] `findings` 为 tuple（或等价不可变序列），不保存可变业务状态。
- [ ] types 层不 import config/repo/service/runtime/ui。
- [ ] pytest 全部通过，无 skip。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未修改 `src/model_deploy/pi05/` 或其他层业务算法。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- 仅用 bool accepted 替代三态 status。
- types 反向依赖 config/service。
- pytest 失败或未解释 skip。

### BLOCKED_ENV

- 缺少 Python3 或 pytest，无法运行测试。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 对应 Gate 场景 | S1 TYPES-RESULT |
| 场景覆盖 | 冻结跨模块 SafetyResult 契约 |
| L2 Gate 依赖本 L3 | 是。后续 service/Gate 均依赖本类型 |
| 未完成影响 | deploy_033/034/035 无法构造合法结果对象 |
