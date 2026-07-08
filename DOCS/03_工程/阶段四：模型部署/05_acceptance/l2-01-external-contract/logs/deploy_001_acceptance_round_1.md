# deploy_001 验收 — Round 1

**结论: PASS_LOCAL**

## 检查项逐条结果

- [x] `contract_result.py` 存在于 `src/model_deploy/act/types/contract_result.py`
- [x] `BundleContractResult` 是 `@dataclass(frozen=True)`，字段: `passed`, `reason`, `missing_files`, `schema_version`
- [x] `NormalizerContractResult` 是 `@dataclass(frozen=True)`，字段: `passed`, `reason`, `expected_dim`, `actual_dim`
- [x] 两个结果对象都有 `is_pass` 属性
- [x] frozen 特性验证通过
- [x] pytest 全部通过 (36/36)
- [x] 产物路径与 L3 声明一致
- [x] 未修改 pi05/、其他层文件或 dispatch

## 验收命令

```bash
PYTHONPATH=src:$PYTHONPATH python3 -m pytest src/model_deploy/act/tests/types/ -v
```

结果: 36 passed
