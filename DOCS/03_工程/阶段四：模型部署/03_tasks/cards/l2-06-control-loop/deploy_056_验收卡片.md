# 验收卡片：deploy_056 L2-01 启动资源与配置接缝修复

> [!info] 归属
> - 所属调度组：l2-06-control-loop
> - 接口 owner：l2-01-external-contract
> - 验收 Agent 只读；不得编辑或 Git。
> - deploy_051/052 的冻结文件与 dispatch 条目必须保持不变。

| L3 编号 | `deploy_056` |
| 验收模式 | `direct-local` |

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-06-control-loop/deploy_056_L2-01启动资源与配置接缝修复.md |
| 源码 | config schema/default、repo canonical resources、facade、config/repo/Gate tests |
| 设计 | L2-01 HTML + agent_context；L1 根 HTML + agent_context 的 owner/协作投影 |
| 前置 | deploy_051/052 PASS_LOCAL，且二者冻结哈希无变化 |

## 2. 必跑命令

```bash
PYTHONPATH=src python3 -m pytest \
  src/model_deploy/act/tests/config \
  src/model_deploy/act/tests/repo \
  src/model_deploy/act/tests/integration/test_l2_01_gate.py -v
```

```bash
python3 skills/stage4-l2-designer/scripts/validate_l2_design_package.py \
  'DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环'
```

## 3. PASS / FAIL / DEFER

### PASS_LOCAL

- [ ] 默认 config 可解析；resource loader 对空/无效 production bundle 稳定失败。
- [ ] loader keyword 开关、YAML 禁止 enabled、独立 observation age、queue=1 均有正负测试。
- [ ] logical camera mapping 无 legacy 双轨。
- [ ] PolicyInputSpec/ActRuntimeResources frozen、唯一派生、public facade additive。
- [ ] metadata/normalizer/config/image/chunk 交叉冲突全部 fail-fast。
- [ ] L2-01 HTML/agent_context 与源码一致；L1 根投影不再留下 owner 断口。
- [ ] deploy_051/052 文件和 dispatch 条目未变化。

### FAIL_LOCAL

任何 Dict/private/第二份 spec、config default 补 production metadata、持久化 command enabled、queue 大于 1、设计双轨、回归失败或冻结文件变化。

### DEFER_TO_L2_GATE

真实 bundle/GPU 只在 local loader 合同已通过后补验；artifact/env 缺失不能替代本卡 PASS_LOCAL。

## 4. L2 Gate 贡献

| 场景 | G02-G03 |
|---|---|
| 贡献 | P0-01～P0-04、P0-06/P0-09 config side、canonical startup resources |
| 未完成影响 | deploy_057/058/053/054/055 不得执行 |

