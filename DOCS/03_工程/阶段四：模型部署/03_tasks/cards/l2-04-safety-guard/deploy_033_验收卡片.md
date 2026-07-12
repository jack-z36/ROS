# 验收卡片：deploy_033 安全检查纯函数微元

> [!info] 归属
> - 所属 L2：`l2-04-safety-guard`
> - 对应 L3：`deploy_033`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_033` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_033_安全检查纯函数微元.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/service/safety_guard.py`、`src/model_deploy/act/tests/service/test_safety_primitives.py`、执行摘要、pytest 输出 |
| 前置条件 | deploy_031、deploy_032 已完成 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 service unit 测试。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_safety_primitives.py -v
```

如果命令无法运行，必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `service/safety_guard.py` 存在且实现 C4、C6-C15（命名可有前缀，但职责一一对应）。
- [ ] INPUT-SHAPE：非 `(16,)` 被拒绝。
- [ ] INPUT-FINITE：NaN/Inf 被拒绝。
- [ ] QUAT-CANDIDATE：零模拒绝；近单位可单位化；内部为 `xyzw`。
- [ ] REFERENCE-ORDER / BOOTSTRAP / MISSING：previous 优先；无 previous 用 observation；都无则 NO_REFERENCE。
- [ ] POSE-TRANSLATION：超限后欧氏距离恰为阈值（方向缩放，非逐轴 clip）。
- [ ] POSE-ROTATION：超限后旋转角恰为阈值；shortest arc / `q` 与 `-q` 处理正确。
- [ ] GRIPPER-RANGE / GRIPPER-STEP：同域投影正确。
- [ ] BIMANUAL-ASSEMBLY：16D 段序不变。
- [ ] OUTPUT-INVARIANT：最终动作仍合法。
- [ ] 无 runtime/ui/ROS/hardware import。
- [ ] pytest 全部通过，无 skip。
- [ ] 未把 A1/B1 完整端到端冒充为本 L3 唯一交付（允许文件中暂无完整 filter_action，但 C 层必须可测）。

### FAIL_LOCAL 条件（任一命中）

- 使用逐轴 component clip 代替三维欧氏投影。
- 无基准时静默放行。
- 把 `wxyz` 硬件序塞进本层。
- 引入 joint limits 或 F100 映射。
- pytest 失败。

### BLOCKED_ENV

- 缺少 Python3、pytest 或 numpy。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 对应 Gate 场景 | S3 service primitives |
| 场景覆盖 | 算法正确性标签 |
| L2 Gate 依赖本 L3 | 是 |
| 未完成影响 | deploy_034 无法可靠编排投影链 |
