# types 层设计：L2-04

## 1. 目标源码路径

```text
src/model_deploy/act/types/safety_result.py
```

本文件服务当前 L2-04 功能边界，不从旧 layer-based L2 卡片继承职责。

## 2. 层职责与文件职责

`types/` 只定义跨 L2 传递的数据语言。此文件承载 C1、C2、C3、C5；不做安全算法、配置读取、ROS 或 runtime 决策。

| 编号 | 数据结构 | 字段/内部存储 | 消费者 |
|---|---|---|---|
| C1 | `SafetyStatus: Enum[str]` | `PASS`、`ADJUSTED`、`REJECTED` | L2-06/L2-05/tests |
| C2 | `SafetyCode: Enum[str]` | `INVALID_SHAPE`、`NON_FINITE`、`INVALID_QUATERNION`、`NO_REFERENCE`、各类调整 code | L2-06/metrics/tests |
| C3 | `SafetyFinding: frozen dataclass` | `code: SafetyCode`、`side: left|right|None`、`before`、`after`、`detail` | C5/L2-06/tests |
| C5 | `SafetyResult: frozen dataclass` | `status`、`action: ActionSpec|None`、`findings: tuple[SafetyFinding,...]` | L2-06/L2-05 |

## 3. 约束与函数设计

不新增行为 Class。四个数据微元均是 value object；必要的 `__post_init__` 只校验：

- `REJECTED` 必须 `action is None`；PASS/ADJUSTED 必须有 action。
- `SafetyFinding.code` 与 status 语义一致。
- `before/after` 仅存可序列化的标量或 tuple，不保存可变 numpy view。

输入是 service 构造时提供的值；输出是冻结跨层契约；副作用为零。

## 4. 依赖方向与验收

- 可依赖：`types/action_spec.py`。
- 禁止依赖：config/repo/service/runtime/ui。
- Pi0.5 参考：`runtime/safety_guard.py::SafetyResult`，仅复用“冻结返回对象”结构。
- 验收：`TYPES-RESULT`；测试 status/action/findings 的合法组合和不可变性。
