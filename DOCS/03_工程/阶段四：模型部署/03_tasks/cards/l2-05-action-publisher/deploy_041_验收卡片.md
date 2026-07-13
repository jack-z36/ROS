# 验收卡片：deploy_041 Action 发布类型与输出配置契约

> [!info] 归属
> - 所属 L2：`l2-05-action-publisher`
> - 对应 L3：`deploy_041`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git。

| L3 编号 | `deploy_041` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-05-action-publisher/deploy_041_Action发布类型与输出配置契约.md` |
| 允许查看 | types/config 目标文件、两个局部测试、执行摘要、pytest 输出 |
| 证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-05-action-publisher/` |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/types/test_action_publish.py \
  src/model_deploy/act/tests/config/test_command_output_config.py \
  src/model_deploy/act/tests/config/test_schema.py -v
```

## 3. PASS / FAIL / BLOCKED

### PASS_LOCAL（全部满足）

- [ ] C1-C6 冻结契约字段与 `03a`/`06_types` 一致，非法组合构造失败。
- [ ] C7 是 frozen config；frame、夹爪范围、deadband、interval、QoS 校验完整。
- [ ] 缺省 `command_output_enabled=False`；显式 bool 可开启；YAML `enabled` 不能静默开启。
- [ ] 新类型与 config 稳定导出，既有 config 回归无失败。
- [ ] 无 ROS/service/runtime/ui/hardware 反向依赖；未把 `RuntimeConfig.mode`/`accepted` 写入新契约。

### FAIL_LOCAL

- 任一 PASS 条件不满足、pytest 失败/无解释 skip、或持久化配置可默认开启 command。

### BLOCKED_ENV

- Python3/pytest/基础依赖缺失，必须写明精确错误；真实 CLI parser 对接是 `downstream-l2`，不得写成已验证。

## 4. L2 Gate 贡献

| 场景 | G01-G03 |
|---|---|
| 贡献 | C1-C7 公共语言、不变量与 CLI default-off 配置契约 |
| 未完成影响 | deploy_042/043/044/045 不得启动 |

