# L3 微元改造任务：command topic 重构 + 删除 Bridge/Mux config

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-02 Config 层重构
来源 Delta：D1（拓扑删 bridge/mux）、D12（发布出口收敛单路 policy_action）
L3 编号：deploy_006
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_006_command重构与删BridgeMux.md`
改造类型：behavior-change
真机风险等级：none
L2 Git 分支：model_deploy-l2-02-config
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config
对应 L2 运行验收场景：[S1, S3]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_006_验收卡片.md
验收模式：direct-local
辅助验收模式：[]
本地验收是否必须：true
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_006
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_006_command重构与删BridgeMux.md
  group: l2-02-config
  branch: model_deploy-l2-02-config
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config
  acceptance_scenarios: [S1, S3]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_006_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs
  wave: 2
  parallel_group: l2-02-config-p2
  depends_on: [deploy_005]
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_007]
  conflict_scope:
    files:
      - src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py
      - src/model_deploy/pi05/common/src/pi05/common/ros/topics.py
    modules:
      - pi05.deploy.config.schema
      - pi05.common.ros.topics
    config_keys:
      - topics.command
      - topics.bridge_output
      - topics.mux
      - bridge
      - mux
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
把 command topic 配置从 AS-IS 的四路关节/手部目标收敛为单路 policy_action，并删除 Bridge/Mux 相关的全部 config 类和解析逻辑（BridgeTopicsConfig/MuxTopicsConfig/BridgeConfig/MuxConfig 及对应解析函数和聚合字段），同步更新 topics.py 的 Pi05CommandTopics。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D1 + D12 |
| 变更对象 | Runtime Topology（删 bridge/mux）+ Action Contract · 发布出口 |
| AS-IS 契约 | `CommandTopicsConfig`（schema.py:118-127）：四路 left/right_arm_joint_target + left/right_hand_target + status + metrics。`BridgeTopicsConfig`（L130-139）、`MuxTopicsConfig`（L142-163）、`BridgeConfig`（L202-214）、`MuxConfig`（L217-228）。`TopicsConfig`（L166-174）含 bridge_output/mux 字段。`DeployConfig`（L239-250）含 bridge/mux 字段。`Pi05CommandTopics`（topics.py:18-38）。 |
| TO-BE 契约 | `CommandTopicsConfig` 改为单路 policy_action + status + metrics。删除 Bridge/Mux 全部 config。`Pi05CommandTopics` 改为 policy_action。依据：TO-BE Contract topic 表 + D1。 |
| 兼容性要求 | 破坏性。 |
| 回滚要求 | git 回退。 |

### 所属 L2 改造工作包

- L2 名称：L2-02 Config 层重构
- 本 L3 在该 L2 中的位置：第二个，依赖 deploy_005（同改 schema.py，串行避免冲突）。
- 本 L3 完成后解锁：deploy_007（runtime/safety）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `CommandTopicsConfig` | schema.py:118-127 | 四路关节/手部目标 | 改为 policy_action 单路 | 是 |
| `_command_topics` | schema.py:365-374 | 解析四路 command | 改为 policy_action | 是 |
| `BridgeTopicsConfig` | schema.py:130-139 | bridge 输出 topic | 删除 | 是 |
| `MuxTopicsConfig` | schema.py:142-163 | mux 仲裁 topic | 删除 | 是 |
| `BridgeConfig` | schema.py:202-214 | bridge 行为配置 | 删除 | 是 |
| `MuxConfig` | schema.py:217-228 | mux 行为配置 | 删除 | 是 |
| `_bridge_topics` | schema.py:377-386 | 解析 bridge topic | 删除 | 是 |
| `_mux_topics` | schema.py:389-426 | 解析 mux topic | 删除 | 是 |
| `_mux_config` | schema.py:453-462 | 解析 mux 配置 | 删除 | 是 |
| `TopicsConfig` | schema.py:166-174 | 含 bridge_output/mux 字段 | 删这两个字段 | 是 |
| `DeployConfig` | schema.py:239-250 | 含 bridge/mux 字段 | 删这两个字段 | 是 |
| `_deploy_from_mapping` | schema.py:267-339 | 解析 bridge_raw/mux_raw + 构造 bridge/mux | 删对应段 | 是 |
| `Pi05CommandTopics` | topics.py:18-38 | 四路默认 topic | 改为 policy_action | 是 |

### 必须保留的现有行为

- frozen dataclass + 解析校验模式。
- `_str`/`_choice` 辅助函数（复用）。
- `from_mapping`/`load_deploy_config` 加载入口（保留，改内部）。

### 已知风险

- 删 Bridge/Mux config 后，`pi05_bridge_node`/`command_mux_node` 失去配置来源——但 TO-BE 这两个节点已停用（D1），所以可接受。
- `_deploy_from_mapping` 删 bridge/mux 段时，注意 `bridge_raw`/`mux_raw` 的提取（L278-279）也要删，否则变量未使用。
- `DeployConfig` 删 bridge/mux 字段后，引用 `config.bridge`/`config.mux` 的上层（bridge_node/mux_node）会报错——但这些节点停用，可接受。

## 6. 真实改造边界

### 本次允许做

**重构 command（保留）：**
- `CommandTopicsConfig`（L118-127）：删 left_arm_joint_target/right_arm_joint_target/left_hand_target/right_hand_target；加 `policy_action: str`；保留 status/metrics。
- `_command_topics`（L365-374）：改解析 policy_action，删四路。
- `Pi05CommandTopics`（topics.py:18-38）：字段改为 policy_action；`with_namespace` 默认 `/pi05/policy_action`；保留 status/metrics。

**删除 Bridge/Mux（删除）：**
- 删 `BridgeTopicsConfig`（L130-139）、`MuxTopicsConfig`（L142-163）、`BridgeConfig`（L202-214）、`MuxConfig`（L217-228）四个类。
- 删 `_bridge_topics`（L377-386）、`_mux_topics`（L389-426）、`_mux_config`（L453-462）三个解析函数。
- `TopicsConfig`（L166-174）：删 `bridge_output`/`mux` 字段。
- `DeployConfig`（L239-250）：删 `bridge`/`mux` 字段。
- `_deploy_from_mapping`（L267-339）：删 bridge_raw/mux_raw 提取（L278-279）+ bridge/mux 构造参数（L326-337 对应段）+ TopicsConfig 的 bridge_output/mux 参数（L322-323）。

### 本次不做

- 不改 `RuntimeConfig`/`SafetyConfig`（deploy_007 做）。
- 不改 deploy.yaml（deploy_008 做）。
- 不补单测（deploy_008 做）。
- 不改 deploy_node（L2-04 做）。
- 不删除 `pi05_bridge_node.py`/`command_mux_node.py` 源文件（保留 git 回滚；只删 config）。

### 明确禁止修改

- 禁止改 `ObservationTopicsConfig`/`_observation_topics`（deploy_005 已改）。
- 禁止改 `RuntimeConfig`/`SafetyConfig`。
- 禁止改通用辅助函数（`_str`/`_choice` 等）。
- 禁止删除 bridge_node/mux_node 源文件（保留回滚路径）。

### Adapter / 直接修改策略

```text
直接修改 + 删除。Bridge/Mux 是 TO-BE 已停用的子系统，config 整体删除（保留源文件作 git 回滚）。command 收敛为单路 policy_action。回滚靠 git。
```

## 7. 实施步骤

1. **改 topics.py 的 `Pi05CommandTopics`**：字段改为 `policy_action`；`with_namespace` 默认 `join_topic(namespace, "policy_action")`；保留 status/metrics。
2. **改 schema.py 的 `CommandTopicsConfig`**（L118-127）：删四路，加 policy_action。
3. **改 `_command_topics`**（L365-374）：解析 policy_action。
4. **删 Bridge/Mux 四个类**（BridgeTopicsConfig/MuxTopicsConfig/BridgeConfig/MuxConfig）。
5. **删三个解析函数**（_bridge_topics/_mux_topics/_mux_config）。
6. **改 `TopicsConfig`**：删 bridge_output/mux 字段。
7. **改 `DeployConfig`**：删 bridge/mux 字段。
8. **改 `_deploy_from_mapping`**：删 bridge_raw/mux_raw 提取、bridge/mux 构造、TopicsConfig 的 bridge_output/mux 参数。
9. **AST 验收**：确认四类四函数已删、policy_action 存在。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
schema = open('src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py', encoding='utf-8').read()
topics = open('src/model_deploy/pi05/common/src/pi05/common/ros/topics.py', encoding='utf-8').read()
# policy_action 存在
assert 'policy_action' in schema and 'policy_action' in topics
# Bridge/Mux 类已删
for cls in ['BridgeTopicsConfig','MuxTopicsConfig','BridgeConfig','MuxConfig']:
    assert f'class {cls}' not in schema, f'{cls} should be removed'
# Bridge/Mux 解析函数已删
for fn in ['_bridge_topics','_mux_topics','_mux_config']:
    assert f'def {fn}' not in schema, f'{fn} should be removed'
# 旧四路 command 字段已删
for f in ['left_arm_joint_target','left_hand_target']:
    assert f not in schema or 'command' not in schema.split(f)[0][-50:], f'old command field {f} in CommandTopicsConfig'
print('deploy_006 验收通过: command收敛policy_action, Bridge/Mux已删')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 类/函数删除断言 | 上述命令通过 |
| dry-run | 否 | — | — |

### 真机风险控制

不适用。

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/
```
## 9. 允许修改

- `src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py`（command + 删 Bridge/Mux）
- `src/model_deploy/pi05/common/src/pi05/common/ros/topics.py`（Pi05CommandTopics）

## 10. 禁止修改

- schema.py 的 ObservationTopicsConfig（deploy_005 已改）、RuntimeConfig、SafetyConfig。
- bridge_node/mux_node 源文件（保留）。
- 通用辅助函数。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`（command topic + 拓扑）
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D1/D12）
3. `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-02-Config层重构.md`

### 必读代码

1. `src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py`
2. `src/model_deploy/pi05/common/src/pi05/common/ros/topics.py`

### 必读约束文档

1. `DOCS/02_约束/工作流/阶段四开发工作流/阶段四模型部署程序改造工作流.md`
2. `DOCS/02_约束/工作流/阶段四开发工作流/attachments/L3微元改造任务模板.md`
3. `DOCS/02_约束/Git协作/Git操作规则.md`
4. `DOCS/02_约束/Git协作/阶段四：模型部署 Git操作规则.md`

### 相关历史任务或执行记录

1. 直接上游：deploy_005（observation 字段，同改 schema.py 已完成）。
2. 同组已完成：deploy_005。

## 12. 执行要求

执行前完成身份校验 + 确认 `depends_on: [deploy_005]` 已完成、`dispatch_status` 非 blocked。

```text
最小复现 / 测试（AST 删除断言）
→ 最小实现（改 command + 删 Bridge/Mux）
→ 验证通过
→ 必要整理
```

## 13. 成功标准

- [x] 已完成任务文件身份校验。
- [x] 已确认当前分支符合所属 L2 分支规范。
- [x] CommandTopicsConfig 收敛为 policy_action。
- [x] Bridge/Mux 四类四函数已删。
- [x] TopicsConfig/DeployConfig 删 bridge/mux 字段。
- [x] _deploy_from_mapping 删对应解析段。
- [x] Pi05CommandTopics 同步更新。
- [x] 已完成自动化验收。
- [x] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：git checkout -- schema.py topics.py
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、修改/删除内容、验收结果、成功标准勾选、真机影响（无）、回滚、未做事项（没改 runtime/safety/deploy.yaml/deploy_node，没删 bridge_node源文件）、后续建议（deploy_007）。

## 16. 执行摘要

### 身份校验

| 校验项 | 结果 |
|--------|------|
| 任务文件路径与 deploy_id | ✅ `deploy_006_command重构与删BridgeMux.md`, id=deploy_006 |
| dispatch YAML task_id | ✅ l2-02-config.yaml: deploy_006 |
| 验收卡片 | ✅ deploy_006_验收卡片.md, mode=direct-local |
| 当前分支 | ✅ model_deploy-l2-02-config |
| 依赖 deploy_005 | ✅ PASS_LOCAL (round_1.md) |
| dispatch_status | ✅ ready |

### 修改的文件

| 文件 | 变更 |
|------|------|
| `src/model_deploy/pi05/common/src/pi05/common/ros/topics.py` | Pi05CommandTopics: 四路字段 → policy_action; with_namespace 生成单路 `/pi05/policy_action` |
| `src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py` | CommandTopicsConfig: 四路 → policy_action; 删 BridgeTopicsConfig/MuxTopicsConfig/BridgeConfig/MuxConfig 四个类; 删 _bridge_topics/_mux_topics/_mux_config 三个函数; TopicsConfig 删 bridge_output/mux; DeployConfig 删 bridge/mux; _deploy_from_mapping 删对应解析段 |

### 验证命令与结果

```bash
# AST 断言（L3 §8）
python3 -c "schema=open('src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py').read(); topics=open('src/model_deploy/pi05/common/src/pi05/common/ros/topics.py').read(); assert 'policy_action' in schema and 'policy_action' in topics; ...; print('deploy_006 验收通过: command收敛policy_action, Bridge/Mux已删')"
```

结果: ✅ `deploy_006 验收通过: command收敛policy_action, Bridge/Mux已删`

```bash
# 导入与 dataclass 行为验证
PYTHONPATH="src/model_deploy/pi05/common/src:src/model_deploy/pi05/deploy/src:$PYTHONPATH" python3 -c "导入 Pi05CommandTopics / CommandTopicsConfig / TopicsConfig / DeployConfig 验证新字段、旧字段删除、frozen、旧类不存在"
```

结果: ✅ `deploy_006 import/dataclass 验证通过`

```bash
# 端到端 YAML 加载
PYTHONPATH="src/model_deploy/pi05/common/src:src/model_deploy/pi05/deploy/src:$PYTHONPATH" python3 -c "load_deploy_config('...deploy.yaml') 验证 command 默认路径等"
```

结果: ✅ `deploy_006 端到端加载验证通过`

### 未验证事项

- deploy.yaml 中 bridge_output/mux/bridge/mux 键尚未更新（deploy_008 处理）。
- deploy_node _create_subscriptions 适配旧 command topic（L2-03 处理）。
- bridge_node/mux_node 源文件未删（保留回滚路径，按 L3 约束不删）。
- RuntimeConfig/SafetyConfig 未改（deploy_007 处理）。

### 结论

**所有成功标准已勾选，三组自动化验证通过。L3 目标达成。建议进入验收 agent 评估 (acceptance card)。**
