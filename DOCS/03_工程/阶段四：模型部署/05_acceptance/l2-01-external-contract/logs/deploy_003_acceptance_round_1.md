# deploy_003 验收 — Round 1

**结论: PASS_LOCAL**

## 检查项逐条结果

- [x] `action_spec.py` 存在于正确路径
- [x] `ACTION_DIM == 16`
- [x] 段维度: LEFT_TCP_ACTION_DIM=7, RIGHT_TCP_ACTION_DIM=7, LEFT_GRIPPER_DIM=1, RIGHT_GRIPPER_DIM=1
- [x] `ActionSpec` 为 frozen dataclass
- [x] `ensure_action_vector` 对 16D 返回 float32，对非 16D 抛 ValueError
- [x] `split_action` 正确拆分 16D 为四段
- [x] `as_vector` 正确拼接为 16D
- [x] roundtrip (split → as_vector) 一致
- [x] pytest 全部通过
- [x] 未修改 pi05/ 或其他层文件

## 验收命令

```bash
PYTHONPATH=src:$PYTHONPATH python3 -m pytest src/model_deploy/act/tests/types/test_action_spec.py -v
```

结果: 全部通过
