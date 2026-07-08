# 验收卡片：deploy_001 契约结果对象 ContractResult

> [!info] 归属
> - 所属 L2：`l2-01-external-contract`
> - 对应 L3：`deploy_001`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_001_契约结果对象ContractResult.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/types/contract_result.py`、`src/model_deploy/act/tests/types/test_contract_result.py`、执行摘要、pytest 输出 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 unit / import 测试。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_contract_result.py -v
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `contract_result.py` 存在于 `src/model_deploy/act/types/contract_result.py`。
- [ ] `BundleContractResult` 是 `@dataclass(frozen=True)`，字段包含 `passed`、`reason`、`missing_files`、`schema_version`。
- [ ] `NormalizerContractResult` 是 `@dataclass(frozen=True)`，字段包含 `passed`、`reason`、`expected_dim`、`actual_dim`。
- [ ] 两个结果对象都有 `is_pass` 属性，返回 `self.passed`。
- [ ] frozen 特性验证通过（修改字段抛 `FrozenInstanceError`）。
- [ ] pytest 全部通过，无 skip。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未修改 `src/model_deploy/pi05/`、其他层文件或 dispatch。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- ContractResult 不是 frozen dataclass。
- 字段缺失或名称不符。
- pytest 失败或有未解释的 skip。
- 修改了禁止修改的文件。
- 把 Pi0.5 的 26D/14D 维度引入 ContractResult。
- 引入了 `blend_steps`/`smoothstep`/`cross_chunk`/`rtc_alignment`/`action_smoothing` 字段。

### BLOCKED_ENV

- 缺少 Python3 或 pytest，无法运行测试。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 影响 L2 Gate | 是 |
| 对应场景 | S1 合法配置载入 |
| 贡献 | 提供契约校验结果对象，是 S1 的结构化输出载体 |
| 仍需后续 L3 | deploy_009 实现契约校验函数后 S1 才完整 |

## 6. 验收结论写入位置

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/deploy_001_acceptance_round_<n>.md
```

结论格式：

```text
结论：PASS_LOCAL / FAIL_LOCAL / BLOCKED_ENV / DEFER_TO_L2_GATE
检查项逐条结果：
- ...
反馈说明：
```
