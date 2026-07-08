# 验收卡片：deploy_003 16D 动作规格 ActionSpec

> [!info] 归属
> - **L1**: model_deploy
> - **L2**: l2-01-external-contract (外部参数加载与契约校验闭环)
> - **L3**: deploy_003
> - **Wave**: 1
> - **Parallel Group**: l2-01-external-contract-p1
> - **验收模式**: direct-local
> - **本地验收必需**: true
> - **真机风险**: none
> - **工作分支**: feat/model_deploy/l2-01-external-contract
> - **集成分支**: model_deploy

---

## 1. 检查对象

| 序号 | 检查项 | 检查方法 | 期望结果 |
|------|--------|---------|---------|
| 1 | 源码文件存在 | 检查文件路径 | `src/model_deploy/act/types/action_spec.py` 存在 |
| 2 | 测试文件存在 | 检查文件路径 | `src/model_deploy/act/tests/types/test_action_spec.py` 存在 |
| 3 | ACTION_DIM 值 | 读取源码 / 导入检查 | `ACTION_DIM == 16` |
| 4 | 段常量定义 | 读取源码 | `LEFT_TCP_ACTION_DIM=7`, `RIGHT_TCP_ACTION_DIM=7`, `LEFT_GRIPPER_DIM=1`, `RIGHT_GRIPPER_DIM=1`，且 7+7+1+1==16 |
| 5 | ActionSpec frozen | 读取源码 / 测试 | `ActionSpec` 使用 `@dataclass(frozen=True)`，字段: `left_tcp_action`, `right_tcp_action`, `left_gripper`, `right_gripper` |
| 6 | ensure_action_vector 合法输入 | 测试 | 接受 16D 向量，返回 np.ndarray float32，shape==(16,) |
| 7 | ensure_action_vector 非法维度 | 测试 | 14D / 15D / 17D 输入均抛出 ValueError |
| 8 | split_action 布局正确 | 测试 | 拆分为 left_tcp_action[0:7] + right_tcp_action[7:14] + left_gripper[14] + right_gripper[15] |
| 9 | pytest 通过 | 运行必跑命令 | 全部测试 PASS，无 FAIL / ERROR |
| 10 | 路径匹配 | 检查文件路径 | 源码在 `src/model_deploy/act/types/action_spec.py`，测试在 `src/model_deploy/act/tests/types/test_action_spec.py` |
| 11 | 未修改 pi05/ | git diff 检查 | `pi05/` 目录无任何变更 |
| 12 | 无 14D / 26D | 读取源码 | 源码中无 `ACTION_DIM=14`、`STATE_DIM=26`、`ARM_DOF=6` 等 Pi0.5 常量 |
| 13 | 无平滑字段 | 读取源码 | 无 `blend_steps` / `smoothstep` / `cross_chunk` / `rtc_alignment` / `action_smoothing` 字段 |

---

## 2. 验收模式

**direct-local**

本任务为纯 types 层定义，无真机风险，采用本地直接验收模式。验收 Agent 在本地环境执行必跑命令并逐项检查第 1 节检查对象。无需真机部署、无需集成环境。

- **验收轮次上限**: 3
- **反馈目录**: `DOCS/03_工程/阶段四：模型部署/03_tasks/feedback/l2-01-external-contract/`
- **验收独立性**: 验收 Agent 独立于执行 Agent，仅依据本卡片检查项验收。

---

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_action_spec.py -v
```

**补充检查命令**（可选，用于辅助验收）:

```bash
# 检查 pi05/ 目录是否被修改
git diff --name-only feat/model_deploy/l2-01-external-contract | grep "^pi05/" || echo "pi05/ 未修改"

# 检查 ACTION_DIM 值
python3 -c "from model_deploy.act.types.action_spec import ACTION_DIM; assert ACTION_DIM == 16, f'ACTION_DIM={ACTION_DIM}'; print('ACTION_DIM=16 OK')"

# 检查无 Pi0.5 常量残留
python3 -c "
import model_deploy.act.types.action_spec as m
import inspect
src = inspect.getsource(m)
for forbidden in ['ARM_DOF', 'HAND_DOF', 'STATE_DIM', 'blend_steps', 'smoothstep', 'cross_chunk', 'rtc_alignment', 'action_smoothing']:
    assert forbidden not in src, f'发现禁止符号: {forbidden}'
print('无禁止符号 OK')
"
```

---

## 4. PASS/FAIL/BLOCKED

### PASS（全部满足）

- [ ] `src/model_deploy/act/types/action_spec.py` 存在
- [ ] `ACTION_DIM == 16`
- [ ] `ActionSpec` 为 frozen dataclass，字段: `left_tcp_action`, `right_tcp_action`, `left_gripper`, `right_gripper`
- [ ] `ensure_action_vector` 接受 16D 向量，返回 np.ndarray
- [ ] `ensure_action_vector` 拒绝非 16D 向量，抛出 ValueError
- [ ] `split_action` 正确拆分为 7+7+1+1 布局
- [ ] pytest 全部通过
- [ ] 文件路径与任务定义匹配
- [ ] 未修改 pi05/ 参考代码
- [ ] 无 14D / 26D / ARM_DOF=6 等 Pi0.5 常量残留
- [ ] 无 blend_steps / smoothstep / cross_chunk / rtc_alignment / action_smoothing 字段

**判定**: 以上全部满足 → **PASS**

### FAIL（任一不满足）

出现以下任一情况 → **FAIL**:
- `action_spec.py` 不存在或路径不符
- `ACTION_DIM != 16`
- `ActionSpec` 不是 frozen dataclass 或字段不正确
- `ensure_action_vector` 未校验维度或未抛 ValueError
- `split_action` 拆分布局错误（非 7+7+1+1）
- pytest 有 FAIL / ERROR
- 修改了 pi05/ 目录
- 存在 14D / 26D / joint angle 语义
- 存在 blend_steps / smoothstep / cross_chunk / rtc_alignment / action_smoothing 字段

**FAIL 处理**: 验收 Agent 将失败项写入 `DOCS/03_工程/阶段四：模型部署/03_tasks/feedback/l2-01-external-contract/deploy_003_feedback_roundN.md`，执行 Agent 修正后重新提交验收。

### BLOCKED（依赖缺失）

出现以下情况 → **BLOCKED**:
- 前置依赖缺失（虽 `depends_on: []`，但环境不可用）
- pytest 无法运行（Python 环境缺失、numpy 未安装等）
- 分支状态异常（不在 `feat/model_deploy/l2-01-external-contract` 分支）

**BLOCKED 处理**: 验收 Agent 记录阻塞原因，通知 L2 负责人解除阻塞后重新验收。

---

## 5. 本 L3 是否影响 L2 Gate

**是**。

| Gate 场景 | 贡献 | 说明 |
|-----------|------|------|
| S1 (合法配置载入) | 是 | `ensure_action_vector` 接受合法 16D 向量，`split_action` 正确拆分为结构化部分 |
| S2 (非法维度失败) | 是 | `ensure_action_vector` 拒绝非 16D 向量（14D/15D/17D），抛出 ValueError |

本 L3 定义 action 16D 契约（`ACTION_DIM=16` + `ActionSpec` + `ensure_action_vector` + `split_action`），是 S1/S2 Gate 场景的维度校验基础。

**注意**: S1/S2 的完整闭环仍需 deploy_009（契约校验）配合。deploy_003 提供底层 ActionSpec 类型和维度常量，deploy_009 在此基础上实现端到端契约校验。deploy_003 单独完成不等于 L2 Gate 通过。

---

## 6. 验收结论写入位置

**验收结论文件**: `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-01-external-contract/deploy_003_验收卡片.md`

验收 Agent 在本文件末尾追加验收结论，格式如下:

```text
## 验收结论

- **验收轮次**: Round N
- **验收结果**: PASS / FAIL / BLOCKED
- **验收时间**: YYYY-MM-DD HH:MM
- **验收 Agent**: (Agent 标识)
- **必跑命令输出**: (pytest 输出摘要)
- **检查项明细**: (逐项 PASS/FAIL)
- **备注**: (如有)
```

验收通过后，在 L3 调度计划中将 `deploy_003` 状态更新为 `accepted`。
