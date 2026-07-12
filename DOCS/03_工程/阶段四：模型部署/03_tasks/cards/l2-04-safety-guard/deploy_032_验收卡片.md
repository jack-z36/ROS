# 验收卡片：deploy_032 SafetyConfig 契约协调

> [!info] 归属
> - 所属 L2：`l2-04-safety-guard`
> - 对应 L3：`deploy_032`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_032` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-04-safety-guard/deploy_032_SafetyConfig契约协调.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-04-safety-guard/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/config/schema.py`、`src/model_deploy/act/config_files/deploy.yaml`、`src/model_deploy/act/tests/config/test_safety_config.py`、`src/model_deploy/act/tests/config/test_schema.py`、执行摘要、pytest 输出 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 config unit 测试。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/config/test_safety_config.py src/model_deploy/act/tests/config/test_schema.py -v
```

如果命令无法运行，必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `SafetyConfig` 含 `max_translation_step_m`、`max_rotation_step_rad`、`gripper_min`、`gripper_max`、`max_gripper_step`、`quaternion_norm_tolerance`（或设计等价且文档一致的字段名）。
- [ ] 平移/旋转阈值 `> 0` 校验生效；非法值拒绝。
- [ ] `gripper_min <= gripper_max` 校验生效。
- [ ] 默认夹爪域不是硬件寄存器风格 `300~1000`。
- [ ] `deploy.yaml` safety 段与新字段一致。
- [ ] 未引入 joint limits 或 F100 寄存器映射逻辑。
- [ ] pytest 相关 config 测试全部通过。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未修改 `src/model_deploy/pi05/` 或 service 安全算法（本任务不应新增 safety_guard 算法）。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- 默认值继续把 F100/`300~1000` 当作模型 action 域。
- 非法阈值被静默接受。
- 把 fallback policy 塞进 SafetyConfig 作为 L2-04 职责。

### BLOCKED_ENV

- 缺少 Python3 或 pytest。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 对应 Gate 场景 | S2 config contract |
| 场景覆盖 | A1 构造所需同域静态 policy |
| L2 Gate 依赖本 L3 | 是 |
| 未完成影响 | deploy_033/034 无法使用正确单位阈值 |
