# deploy_002 验收 — Round 1

**结论: PASS_LOCAL**

## 检查项逐条结果

- [x] `state_spec.py` 存在于正确路径
- [x] `STATE_DIM == 16`
- [x] `StateSpec` 为 frozen dataclass，携带段名/段维度/段偏移元数据
- [x] 四段维度: LEFT_TCP_POSE_DIM=7, RIGHT_TCP_POSE_DIM=7, LEFT_GRIPPER_WIDTH_DIM=1, RIGHT_GRIPPER_WIDTH_DIM=1
- [x] `ensure_state_vector` 对 16D 返回 float32，对非 16D 抛 ValueError
- [x] `encode_state` 输出 16D float32，布局正确
- [x] pytest 全部通过
- [x] 未修改 pi05/ 或其他层文件
- [x] 无 26D/14D 残留，无关节角语义字段

## 验收命令

```bash
PYTHONPATH=src:$PYTHONPATH python3 -m pytest src/model_deploy/act/tests/types/test_state_spec.py -v
```

结果: 全部通过
