# 验收反馈报告：deploy_041 Action 发布类型与输出配置契约

- 验收轮次：1
- 验收模式：`direct-local`
- 验收 sub-agent：只读，未改源码/测试/dispatch/卡片/Git
- 结论：**PASS_LOCAL**

## 1. 结论

`PASS_LOCAL` —— 所有本地必跑检查以真实命令输出通过。

> 主 Agent 注意：结论为 `PASS_LOCAL`，须将本 L3 任务文件从
> `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_041_Action发布类型与输出配置契约.md`
> 移动到
> `DOCS/03_工程/阶段四：模型部署/03_tasks/completed/l2-05-action-publisher/deploy_041_Action发布类型与输出配置契约.md`
> （含同一原子提交内的实现、执行摘要、本反馈）。验收 sub-agent 不执行移动。

## 2. PASS 条件核对

| 条件 | 结果 | 证据 |
|---|---|---|
| C1-C6 冻结契约字段，非法组合构造失败 | PASS | 见 §3 测试 G01（42 项）+ 代码 `action_publish.py` |
| C7 是 frozen config；frame/夹爪范围/deadband/interval/QoS 校验完整 | PASS | 见 §3 测试 G02/G03（18 项）+ `schema.py` `__post_init__` |
| 缺省 `command_output_enabled=False`；显式 bool 可开启；YAML `enabled` 不能静默开启 | PASS | `test_command_output_config.py` 全过 |
| 新类型与 config 稳定导出，既有 config 回归无失败 | PASS | import 烟雾测试 `IMPORT OK` + `test_schema.py` 全过 |
| 无 ROS/service/runtime/ui/hardware 反向依赖；未把 `RuntimeConfig.mode`/`accepted` 写入新契约 | PASS | 见 §4 静态核查 |

## 3. 必跑命令真实输出

### 3.1 pytest（3 个测试文件）

```text
$ PYTHONPATH=src python3 -m pytest \
    src/model_deploy/act/tests/types/test_action_publish.py \
    src/model_deploy/act/tests/config/test_command_output_config.py \
    src/model_deploy/act/tests/config/test_schema.py

============================== 78 passed in 0.10s ==============================
```

- `test_action_publish.py`：42 passed —— C1-C6 合法/非法/frozen/tuple 边界/组合不变量（含 REJECTED/OBSERVED/BLOCKED→count 0、PUBLISHED→plan completed、PARTIAL→count>0 且未完成、driver_accepted/hardware_reached 恒为 None）。
- `test_command_output_config.py`：18 passed —— C7 默认关闭、显式开启、持久化 `enabled` 拒绝（True 与 False 均拒绝）、缺段默认、YAML `command_output_enabled` 键不生效、frame/夹爪域/deadband/interval/QoS 参数校验。
- `test_schema.py`：18 passed —— 既有 config 回归，无失败。

### 3.2 导入烟雾测试

```text
$ PYTHONPATH=src python3 -c "from model_deploy.act.types.action_publish import *; from model_deploy.act.config.schema import DeployConfig; print('IMPORT OK')"

IMPORT OK
```

## 4. 静态核查（G01-G03 场景）

- **C1-C6 冻结 + 组合不变量失败于非法组合**：`action_publish.py` 中 C1-C6 均为 `@dataclass(frozen=True)`（C5 为 `str Enum`），`__post_init__` 在构造期校验不变量，测试中非法组合均抛 `ValueError`/`TypeError`。✓
- **C7 默认关闭 + 显式 bool + YAML 不能开启**：`CommandOutputConfig.command_output_enabled` 默认 `False`；`DeployConfig.from_mapping(..., command_output_enabled=...)` 仅由启动调用方传入；`_command_output_from_mapping` 中 `if "enabled" in command_output_raw: raise DeployConfigError`（与值无关，True/False 都拒绝）。✓
- **稳定导出**：`types/__init__.py` 导出 C1-C6，`config/__init__.py` 导出 `CommandOutputConfig`/`DeployConfig`。✓
- **无反向依赖 / 未写入 forbidden 字段**：`action_publish.py` 仅 `import math, dataclasses, enum, typing` 与 `from .safety_result import SafetyResult, SafetyStatus`；无任何 `rclpy`/`rospy`/`roslib` 或 `repo/service/runtime/ui` 导入；不引用 `RuntimeConfig.mode`，不引入 `accepted: bool` 状态机或原始 deadman/gate 字段（`driver_accepted`/`hardware_reached` 显式强制为 `None`）。✓
- **deploy.yaml 未持久化 enabled**：`command_output:` 段仅含静态映射（pose_frame_id/gripper_*/deadband/interval/qos_depth），无 `enabled:` 键（仅注释说明其有意缺失）。✓

## 5. 失败项

无。

## 6. 修复请求（给执行 sub-agent）

无。`PASS_LOCAL`，无需返回执行 Agent 修正。

## 7. 未验证项（登记，非失败）

- **L2-06 CLI 真实对接**：`--enable-command-output` 显式 bool 覆盖路径（属 L2-06 启动装配）本 L3 未实现/未运行；仅验证了 `from_mapping(command_output_enabled=True)` 装配开关可用。属下游 L2 Gate 贡献。
- **ROS / 真机**：本 L3 无 ROS、publisher、硬件副作用，不涉 real-robot 验证。
- **B1/B2/B3**：下游消费 C4/C1/C2/C7 的产出逻辑不在本 L3 范围。

## 8. 回滚登记

由主 Agent 按实际 diff 回退：删除 `src/model_deploy/act/types/action_publish.py` 及两个新测试文件；还原 `types/__init__.py`、`config/__init__.py`、`schema.py`、`deploy.yaml` 的本 L3 改动。本 L3 不做 Git 操作。
