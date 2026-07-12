# ACT 微元设计与协作：L2-04

## 1. 设计结论

ACT 版不是把 Pi0.5 的关节 Guard 改名，而是以 `A1 → B → C` 实现绝对 TCP 目标的单步安全投影。完整编号见 `03a_功能微元总览与组织结构.md`。

| 结论 | 已确认设计 |
|---|---|
| 输入域 | 已解归一化的部署 ActionDomain；L2-04 不做尺度恢复或硬件转换 |
| pose | 绝对目标；内部位置米制、四元数 `xyzw`、坐标系必须与 observation 相同 |
| 基准 | previous safe action 优先；fresh observation 仅作启动/重置兜底；都没有即拒绝 |
| 投影 | 平移欧氏距离、旋转最短弧、夹爪范围与单步变化 |
| 输出 | `SafetyResult(PASS/ADJUSTED/REJECTED)`；fallback 仍属 L2-06 |

## 2. ACT 微元设计表

| 编号 | ACT 微元 | 3.5 类型 | 落点 | 输入 | 输出 | 副作用 | Pi0.5 参考 |
|---|---|---|---|---|---|---|---|
| A1 | `SafetyGuard` | 3.25 class | `service/safety_guard.py` | immutable config | 可调用 guard | 无运行时状态 | `SafetyGuard` 结构复用 |
| B1 | `filter_action` | 编排 | 同上 | candidate/reference/config | C5 | 无 | `filter_action` 骨架复用 |
| B2 | `_validate_candidate_action` | 编排 | 同上 | candidate 16D | canonical ActionSpec | 无 | shape→finite→split 结构复用 |
| B3 | `_project_arm_pose` | 编排 | 同上 | target pose/reference pose | safe pose/findings | 无 | delta 限制思想；算法重写 |
| B4 | `_project_gripper` | 编排 | 同上 | target/reference scalar | safe scalar/findings | 无 | hand clip 结构参考 |
| B5 | `_project_bimanual_action` | 编排 | 同上 | candidate/reference | safe ActionSpec/findings | 无 | structured output 结构参考 |
| C1-C5 | 结果与内部数据 | 数据 | `types/`、service 私有 | 字段 | 冻结 RAM 对象 | 无 | `SafetyResult` 结构复用 |
| C6-C15 | 原子计算 | 计算函数 | `service/safety_guard.py` | RAM 对象 | RAM 对象/错误 | 无 | 分别见 `02` §2 |

## 3. 内部协作契约

```text
Creation order:
  L2-01 构造并校验 ActionDomain/SafetyConfig
  L2-06 创建 A1 SafetyGuard

State owner:
  A1 只持有 immutable config。
  L2-06 持有 previous_safe_action；L2-02 持有 observation；L2-06 持有 metrics/fallback。

Pure RAM calculations:
  B1-B5 与 C1-C15 都是 RAM 内同步计算。

External boundary reads/writes:
  无。ROS/hardware/file 读写均不进入 L2-04。

Runtime orchestration point:
  L2-06 ControlLoop.tick() 同步调用 B1；B1 不是 timer 或 fallback 编排。

Failure propagation:
  C6/C7/C8/C9/C15 的契约失败 → B1 构造 C5(REJECTED) → L2-06 fallback。
  C10-C13 的可投影越界 → C3 finding → C5(ADJUSTED) → L2-06 可发布。
```

## 4. Status 语义

| 状态 | `action` | 产生条件 | L2-06 行为 |
|---|---|---|---|
| PASS | 原样 ActionSpec | 没有 finding | 交 L2-05 |
| ADJUSTED | 投影后 ActionSpec | 发生 C10-C13 的安全调整 | 交 L2-05，并记录调整 |
| REJECTED | `None` | 输入契约、reference 或最终不变量失败 | 进入 L2-06 fallback |

不得把 ADJUSTED 视为 fallback，不得让 L2-04选择 fallback 策略。
