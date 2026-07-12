# L2-04 整体验收卡片：单步 Action 安全检查闭环

> [!info] 归属
> - 所属 L2：`l2-04-safety-guard`
> - 设计目录：`DOCS/03_工程/阶段四：模型部署/02_implement/l2-04-safety-guard_单步Action安全检查闭环/`
> - 验收模式：`direct-local`（Gate 基础环境：CPU + mock RAM，无 ROS/硬件）
> - 可选补验：`downstream-l2`（L2-06 mock 分流）、`hardware-blocked`（L2-05 shadow/real-robot）
> - 验收轮次上限：3

## 1. 验收目标

证明两件事同时成立：

1. A1/B1-B5/C1-C15 能在 mock RAM 环境中，把已解归一化的 16D 绝对候选动作稳定分为 PASS、ADJUSTED、REJECTED，并返回带稳定原因码的 `SafetyResult`。
2. 实现没有把 previous 状态所有权、fallback、ROS 发布、硬件 gate、F100 寄存器映射或关节限位带入 L2-04。

## 2. Required L3 清单

| L3 | 标题 | 验收模式 | Gate 场景 |
|---|---|---|---|
| deploy_031 | SafetyResult 类型定义 | direct-local | S1 TYPES-RESULT |
| deploy_032 | SafetyConfig 契约协调 | direct-local | S2 config contract |
| deploy_033 | 安全检查纯函数微元 | direct-local | S3 service primitives |
| deploy_034 | SafetyGuard 编排与入口 | direct-local | S4 service orchestration |
| deploy_035 | L2-04 Gate 集成测试与验收脚本 | direct-local | S1-S5 全量 |

## 3. Gate 场景总览

### S1：类型契约（TYPES-RESULT）

三种 status 的字段组合冻结且完整；REJECTED 必须 `action is None`。

### S2：配置契约

SafetyConfig 与部署 ActionDomain 同域：米、弧度、夹爪训练域、四元数容差；非法范围拒绝；非 F100 默认。

### S3：纯函数算法

INPUT / REFERENCE / POSE / GRIPPER / BIMANUAL / OUTPUT-INVARIANT 标签在独立单测中 PASS。

### S4：编排入口

A1.filter_action 返回正确三态；无跨 tick 业务状态；不 fallback。

### S5：完整 mock Gate 与边界

`l2_04_verify.sh` 全标签 PASS；PURITY-IMPORT 确认无 runtime/ui/ROS/hardware/repo loader。

## 4. 验收运行目录

```text
仓库根目录
```

## 5. 最低验证层级

`unit` + `import` + `mock`（无 ROS、无硬件、无真实 policy）

## 6. 运行命令

```bash
bash "DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/scripts/l2_04_verify.sh"
```

## 7. 测试输入

- 合法 16D 绝对候选动作（物理域 float）
- previous_safe_action / ObservationSnapshot mock 基准
- 非法 shape、NaN/Inf、非法 quaternion、无基准
- 超平移阈值、超旋转阈值、超夹爪范围/步长

## 8. 观察点

| 标签 | 观察内容 | PASS 含义 |
|---|---|---|
| TYPES-RESULT | status/action/findings | 契约冻结 |
| INPUT-* | 输入校验 | 非法拒绝 |
| REFERENCE-* | 基准选择 | previous→obs→NO_REFERENCE |
| POSE-* | 平移/旋转投影 | 阈值恰达、几何正确 |
| GRIPPER-* | 夹爪同域投影 | 范围与步长正确 |
| RESULT-STATUS | 三态 | PASS/ADJUSTED/REJECTED 正确 |
| PURITY-IMPORT | import 扫描 | 无 runtime/ui/ROS/hardware |

## 9. 通过现象

- `l2_04_verify.sh` 退出码 0
- 全部核心标签 PASS，无 FAIL
- 核心标签无 BLOCKED
- L2-06 仅凭 `SafetyResult.status` 可决定发布或 fallback（接口语义层面）

## 10. 失败现象与排查入口

| 失败现象 | 排查入口 |
|---|---|
| types 测试失败 | `tests/types/test_safety_result.py` |
| config 测试失败 | `tests/config/test_safety_config.py` |
| primitives 失败 | `tests/service/test_safety_primitives.py` |
| 编排失败 | `tests/service/test_safety_guard.py` |
| Gate/边界失败 | `tests/integration/test_l2_04_gate.py`、`service/safety_guard.py` import 扫描 |

## 11. 未验证项处理方式

| 未验证项 | 处理方式 |
|---|---|
| L2-06 真实 ControlLoop 集成 | `downstream-l2`：L2-06 设计/实现阶段补验 |
| L2-05 shadow-run / topic | `downstream-l2` / shadow |
| real-robot / 急停 / hardware gate | `hardware-blocked`：属 L2-05 与人类授权 |
| 真实机械臂可达/IK/碰撞 | 不适用本 L2 |

## 12. 是否允许进入下游 L2

L2-04 mock Gate 通过后，允许 L2-06 集成 `SafetyGuard.filter_action`，允许 L2-05 消费 `SafetyResult.action` 做外部适配设计。

## 13. 是否允许触发 Git 合入

满足以下全部条件才允许合入：

- 全部 5 个 L3 达到可解释终态（PASS_LOCAL 或明确 DEFER）
- L2 Gate 通过（本卡片核心场景 PASS）
- 人类验收签字通过
- 不允许合入：runtime 状态机、fallback 策略、ROS/hardware 代码、关节限位、F100 反推为输入域

## 14. 人类验收签字入口

L2-04 Gate 完成后，将人类验收结论写入：

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/验收结果.md
```

格式参见 `agent_context/05_人类验收机制.md`。
