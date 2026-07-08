# 验收卡片：deploy_002 16D 状态规格 StateSpec

> [!info] 归属
> - 所属 L2：`l2-01-external-contract`
> - 对应 L3：`deploy_002`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

## 1. 检查对象

| 检查项 | 路径 |
| --- | --- |
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/deploy_002_16D状态规格StateSpec.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/evidence/deploy_002/` |
| 允许查看的产物 diff | `src/model_deploy/act/types/state_spec.py`、`src/model_deploy/act/tests/types/test_state_spec.py`、`src/model_deploy/act/types/__init__.py`、`src/model_deploy/act/tests/types/__init__.py` |
| 允许查看的日志 | `evidence/deploy_002/pytest_state_spec.log` |

## 2. 验收模式

`direct-local`

本 L3 真机风险为 `none`，全部验收在本地以只读方式完成，无须真机或集成环境。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_state_spec.py -v
```

验收 Agent 须在仓库根目录 `/home/hit/ROS/worktrees/l2-01` 下以只读方式执行该命令，并将完整输出与执行 Agent 归档的 `pytest_state_spec.log` 比对一致。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件

- [ ] `src/model_deploy/act/types/state_spec.py` 存在于正确路径
- [ ] `STATE_DIM == 16`
- [ ] `StateSpec` 为 frozen dataclass，携带段名 / 段维度 / 段偏移元数据
- [ ] 四段维度分别为 `LEFT_TCP_POSE_DIM=7`、`RIGHT_TCP_POSE_DIM=7`、`LEFT_GRIPPER_WIDTH_DIM=1`、`RIGHT_GRIPPER_WIDTH_DIM=1`
- [ ] `ensure_state_vector` 对 16D 输入返回 float32 `np.ndarray`
- [ ] `ensure_state_vector` 对非 16D（如 15、17）输入抛 `ValueError`
- [ ] `encode_state` 输出 16D float32 `np.ndarray`，布局为 left_tcp_pose(7)+right_tcp_pose(7)+left_gripper_width(1)+right_gripper_width(1)
- [ ] pytest 全部通过、无 skip
- [ ] 产物路径与 L3 声明一致（仅两个目标文件 + 必要 `__init__.py` 导出）
- [ ] 未修改 `pi05/` 或 config / repo / service / runtime / ui 层文件
- [ ] 无 26D / 14D Pi0.5 维度残留
- [ ] 无 `blend_steps` / `smoothstep` / `cross_chunk` / `rtc_alignment` / `action_smoothing` 字段
- [ ] 无关节角语义字段（`arm_q` / `hand_q`）

### FAIL_LOCAL 条件

满足以下任一即判 FAIL_LOCAL：
- `state_spec.py` 不存在或路径不符
- `STATE_DIM != 16`，或出现 26D / 14D 维度
- `StateSpec` 非 frozen 或缺失段元数据
- `ensure_state_vector` 未对非 16D 输入抛 `ValueError`
- `encode_state` 输出维度非 16 或段布局错误
- pytest 存在失败或 skip
- 修改了 `pi05/` 或其他层文件
- 出现 `blend_steps` / `smoothstep` / `cross_chunk` / `rtc_alignment` / `action_smoothing` 字段
- 出现关节角语义字段

### BLOCKED_ENV

满足以下任一即判 BLOCKED_ENV（不计入验收轮次）：
- 仓库中缺失 `python3` 可执行
- 缺失 `pytest` 或 `numpy` 依赖，且非本 L3 产物原因
- 必跑命令因环境原因无法执行（非代码错误）

## 5. 本 L3 是否影响 L2 Gate

| 项 | 内容 |
| --- | --- |
| 是否影响 L2 Gate | 是 |
| 影响场景 | S1（合法配置载入）+ S2（非法维度失败） |
| 贡献 | 提供 `state_dim=16` 契约常量、`StateSpec` 段定义、`ensure_state_vector` 维度校验、`encode_state` 拼接函数 |
| 是否可独立闭环 | 否，S1/S2 完整闭环仍需 `deploy_008`（RuntimeConfig 引用 state_dim）与 `deploy_009`（契约校验引用 ensure_state_vector）在集成分支联调 |

## 6. 验收结论写入位置

验收结论写入：

```
DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-01-external-contract/evidence/deploy_002/验收结论.md
```

结论文件须包含：验收轮次、判定结果（PASS_LOCAL / FAIL_LOCAL / BLOCKED_ENV）、逐条核对结果、必跑命令输出摘要、验收 Agent 签名时间。若为 FAIL_LOCAL，须列出具体失败项与证据引用。
