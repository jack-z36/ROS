# L2 整体验收卡片：l2-01-external-contract

> [!info] 归属
> - 所属 L2：`l2-01-external-contract`（外部参数加载与契约校验闭环）
> - 验收模式：`direct-local` + `static-review`
> - 验收轮次上限：3
> - 本卡片用于 L2 Gate 验收，在全部 required L3 达到可解释状态后由 L2 验收 Agent 执行。
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

## 1. 检查对象

| 字段 | 值 |
|---|---|
| L2 设计目录 | `DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环/` |
| L2 功能边界 | `agent_context/01_L2功能边界.md` |
| L2 验收机制 | `agent_context/04_L2验收机制.md` |
| L2 人类验收机制 | `agent_context/05_人类验收机制.md` |
| dispatch 索引 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/dispatch/l2-01-external-contract.yaml` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/` |
| required L3 | deploy_001 ~ deploy_010（共 10 个） |

## 2. required L3 清单与状态

| L3 | 标题 | wave | 验收模式 | 预期终态 |
|---|---|---|---|---|
| deploy_001 | 契约结果对象 ContractResult | 1 | direct-local | PASS_LOCAL |
| deploy_002 | 16D 状态规格 StateSpec | 1 | direct-local | PASS_LOCAL |
| deploy_003 | 16D 动作规格 ActionSpec | 1 | direct-local | PASS_LOCAL |
| deploy_004 | manifest 解析器 | 2 | direct-local | PASS_LOCAL |
| deploy_005 | normalizer 加载器 | 2 | direct-local | PASS_LOCAL |
| deploy_006 | experiment_config 加载器 | 2 | direct-local | PASS_LOCAL |
| deploy_007 | bundle 读取器 | 2 | direct-local | PASS_LOCAL |
| deploy_008 | DeployConfig 核心 schema 与校验器 | 3 | direct-local | PASS_LOCAL |
| deploy_009 | 契约交叉校验与配置编排 | 4 | direct-local | PASS_LOCAL |
| deploy_010 | L2 Gate 集成测试 | 5 | direct-local | PASS_LOCAL |

## 3. L2 Gate 验收项

| 验收项 | 验证层级 | 测试输入 | 观察点 | 通过现象 | 失败现象 |
|---|---|---|---|---|---|
| S1 合法配置载入 | unit / import | mock deploy.yaml + mock bundle | stdout / pytest | `DeployConfig`、`StateSpec`、`ActionSpec` 构造成功 | 抛异常或字段缺失 |
| S2 非法维度失败 | unit | state/action dim 非 16 | exception | 抛明确配置异常 | 静默通过 |
| S3 bundle 缺文件失败 | unit | 缺 manifest/normalizers/checkpoint | exception | 抛明确文件/契约异常 | 进入半初始化 |
| S4 normalizer 维度不一致失败 | unit | normalizer 长度非 16 | ContractResult / exception | 失败原因可读 | 无明确原因 |
| S5 无平滑配置泄漏 | static-review | schema/default yaml/docs | `rg` 输出 | 不存在 smoothstep/blend/cross-chunk/RTC 平滑字段 | 出现第一版外平滑配置 |

## 4. 必跑命令

```bash
# 全量单测
python3 -m pytest src/model_deploy/act/tests/types src/model_deploy/act/tests/config src/model_deploy/act/tests/repo src/model_deploy/act/tests/integration -v

# 无平滑配置泄漏检查
rg -n 'smoothstep|blend_steps|cross_chunk|rtc_alignment|action_smoothing' src/model_deploy/act DOCS/03_工程/阶段四：模型部署/02_implement/l2-01-external-contract_外部参数加载与契约校验闭环
```

## 5. PASS / FAIL 判断标准

### L2 Gate PASS 条件（全部满足）

- [ ] 全部 10 个 required L3 达到可解释状态（`PASS_LOCAL` 或 `DEFER_TO_L2_GATE`）。
- [ ] S1 合法配置载入：mock deploy.yaml + mock bundle 能构造 `DeployConfig`、`StateSpec`、`ActionSpec`。
- [ ] S2 非法维度失败：state/action dim 非 16 时抛明确异常。
- [ ] S3 bundle 缺文件失败：缺 manifest/normalizers/checkpoint 时抛明确异常。
- [ ] S4 normalizer 维度不一致失败：normalizer 长度非 16 时返回可读失败原因。
- [ ] S5 无平滑配置泄漏：`rg` 检查源码和配置中不存在 `smoothstep`/`blend_steps`/`cross_chunk`/`rtc_alignment`/`action_smoothing`（设计文档中仅出现在"禁止/不负责/去除"语境）。
- [ ] 全量 pytest 通过，无未解释的 skip 或 xfail。
- [ ] 未修改 `src/model_deploy/pi05/`、`pi05_old/` 或 `_legacy_layer_based_act/`。

### L2 Gate FAIL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- 任一 required L3 处于 `FAIL_LOCAL` 且未在 3 轮内修复。
- 文档或 schema 暗含第一版外平滑配置。
- 下游零猜测失败：后续 L2 无法从 L2-01 产出的对象读取 state/action/topic/bundle 契约。

## 6. 下游放行

L2-01 Gate 通过后：

- 允许 L2-02 使用 state/topic/image/config 契约。
- 允许 L2-03 使用 bundle/normalizer/runtime 契约。
- 允许 L2-06 使用 chunk/cursor/fallback 的最小静态配置。

## 7. 不允许合入条件

- Gate 未证明非法配置会失败。
- 文档或 schema 暗含第一版外平滑配置。
- 人类验收未签字。

## 8. 验收结论写入位置

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/验收结果.md
```

L2 Gate 结论格式：

```text
## L2 Gate 验收

- 验收 Agent：
- 验收日期：YYYY-MM-DD
- Gate 结论：[ ] 通过  [ ] 不通过
- S1 合法配置载入：[ ] 通过
- S2 非法维度失败：[ ] 通过
- S3 bundle 缺文件失败：[ ] 通过
- S4 normalizer 维度不一致失败：[ ] 通过
- S5 无平滑配置泄漏：[ ] 通过
- required L3 状态汇总：
  - deploy_001：<终态>
  - deploy_002：<终态>
  - ...
  - deploy_010：<终态>
- 备注：
```
