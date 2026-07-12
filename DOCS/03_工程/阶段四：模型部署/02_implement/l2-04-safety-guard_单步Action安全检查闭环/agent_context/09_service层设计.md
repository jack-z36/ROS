# service 层设计：L2-04

## 1. 目标源码路径

```text
src/model_deploy/act/service/safety_guard.py
```

`service/` 承载 A1、B1-B5、C4、C6-C15。它只做 RAM 内业务计算；不得 import runtime/ui/ROS/hardware。

## 2. Class 设计

| Class | 封装编号 | 内部状态 | 生命周期 | 为什么是 class |
|---|---|---|---|---|
| A1 `SafetyGuard` | B1-B5，静态 policy | immutable `SafetyConfig`/ActionDomain | L2-06 启动装配一次，每 tick 同步调用 | 多次调用共享同一安全策略；不拥有业务状态 |

`SafetyGuard` 不是持久状态机。`previous_safe_action`、snapshot、metrics、fallback 都通过 B1 参数输入或留在 L2-06。

## 3. B 层编排函数

| 编号 | 函数 | 输入 | 输出 | 调用 C/B | 错误行为 |
|---|---|---|---|---|---|
| B1 | `filter_action` | candidate、previous、snapshot | C5 `SafetyResult` | B2、C9、B5 | 捕获契约失败并返回 REJECTED |
| B2 | `_validate_candidate_action` | candidate 16D | canonical `ActionSpec` | C6-C8、`split_action` | shape/finite/quat 失败 |
| B3 | `_project_arm_pose` | target/reference pose | safe pose + findings | C10-C11 | 不拒绝；可投影则 finding |
| B4 | `_project_gripper` | target/reference scalar | safe value + findings | C12-C13 | 不拒绝；可投影则 finding |
| B5 | `_project_bimanual_action` | candidate/reference | safe ActionSpec + findings | B3×2、B4×2、C14-C15 | 最终不变量失败 |

## 4. C 层计算函数

| 编号 | 函数/数据 | 输入 | 输出 | 副作用 |
|---|---|---|---|---|
| C4 | `_ComparisonReference` | source + pose/gripper fields | 内部 frozen 基准 | 无 |
| C6 | `require_action_vector_16` | object | exact `(16,)` ndarray | 无 |
| C7 | `require_finite_action` | vector | validated vector | 无 |
| C8 | `canonicalize_quaternion` | `xyzw(4,)`、tol | unit quaternion | 无 |
| C9 | `select_comparison_reference` | previous/snapshot | C4 或 NO_REFERENCE | 无 |
| C10 | `limit_translation_step` | xyz/ref/limit m | projected xyz + finding | 无 |
| C11 | `limit_rotation_step` | quat/ref/limit rad | slerp quat + finding | 无 |
| C12 | `clamp_gripper_range` | scalar/min/max | projected scalar + finding | 无 |
| C13 | `limit_gripper_step` | scalar/ref/max step | projected scalar + finding | 无 |
| C14 | `build_safe_action` | left/right fields | ActionSpec | 无 |
| C15 | `validate_safe_action_invariants` | ActionSpec/domain | validated ActionSpec | 无 |

## 5. 算法边界

- C10：`target-ref` 的三维范数超限时沿同一方向缩放到阈值，绝不逐轴裁剪。
- C11：使用 quaternion shortest arc；`q` 与 `-q` 表示同一姿态，必须避免长弧跳变。
- C12/C13：输入和阈值必须在同一部署 ActionDomain；L2-04 不知道也不关心 F100 寄存器值。
- C8/C15：只处理内部 `xyzw`，禁止在本层 reorder。

## 6. 依赖、Pi0.5 与验收

- 允许依赖：types、config、numpy；复用 `ActionSpec/split_action`。
- 禁止依赖：runtime、ui、ROS、hardware SDK、repo loader。
- Pi0.5：复用 Guard/入口/anchor 的结构，不复用 joint limit 或 component clip。
- 验收：`04_L2验收机制.md` 的所有 service 标签与 `PURITY-IMPORT`。
