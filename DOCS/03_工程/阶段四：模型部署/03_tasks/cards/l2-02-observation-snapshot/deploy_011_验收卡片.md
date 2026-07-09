# 验收卡片：deploy_011 观测类型定义 ObservationTypes

> [!info] 归属
> - 所属 L2：`l2-02-observation-snapshot`
> - L3 编号：`deploy_011`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_011` |
| 验收模式 | `direct-local` |
## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_011_观测类型定义ObservationTypes.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/types/observation.py`、`src/model_deploy/act/tests/types/test_observation.py`、执行摘要、pytest 输出 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 unit / import 测试。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/types/test_observation.py -v
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `observation.py` 存在于 `src/model_deploy/act/types/observation.py`。
- [ ] `ObservationState` 是 `@dataclass(frozen=True)`，字段含 left_tcp_position、left_tcp_orientation、left_gripper_width、right_tcp_position、right_tcp_orientation、right_gripper_width。
- [ ] `ObservationSnapshot` 是 `@dataclass(frozen=True)`，字段含 images、state、encoded_state、captured_at_s。
- [ ] `ObservationSnapshot.__post_init__` 校验 `encoded_state.shape == (16,)`，非法维度抛 ValueError。
- [ ] `ObservationFreshnessResult` 是 `@dataclass(frozen=True)`，字段含 missing_fields、stale_fields、field_ages_s、ready。
- [ ] frozen 特性验证通过（修改字段抛 FrozenInstanceError）。
- [ ] 无 ROS 环境下 `from act.types.observation import ObservationState, ObservationSnapshot, ObservationFreshnessResult` 成功。
- [ ] pytest 全部通过，无 skip。
- [ ] 产物路径与 L3 声明一致（types/observation.py + tests/types/test_observation.py）。
- [ ] 未修改 `src/model_deploy/act/config/`、`src/model_deploy/act/repo/`、`src/model_deploy/pi05/` 或其他层文件。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- ObservationSnapshot 接受非法维度 encoded_state（如 shape (26,)）。
- types/observation.py import 了 config/repo/service/runtime/ui 层模块。
- ObservationState 使用 26D 或旧 joint position 语义。
- 修改了禁止修改的文件。
- pytest 失败或有未解释的 skip。

### BLOCKED_ENV

- 缺少 Python3 或 pytest，无法运行测试。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 影响 L2 Gate | 是 |
| 对应场景 | S1 Mock 全字段 snapshot 组装 |
| 贡献 | 定义 ObservationSnapshot 的 16D 数据契约，下游可 import 类型而不依赖 L2-02 service/runtime |
| 仍需后续 L3 | deploy_002 实现 collector 组装 snapshot、deploy_004 实现 buffer 存储、deploy_006 端到端集成验证 |

## 6. 验收结论写入位置

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs/deploy_011_acceptance_round_<n>.md
```

结论格式：

```text
结论：PASS_LOCAL / FAIL_LOCAL / BLOCKED_ENV / DEFER_TO_L2_GATE
检查项逐条结果：
- ...
反馈说明：
```
