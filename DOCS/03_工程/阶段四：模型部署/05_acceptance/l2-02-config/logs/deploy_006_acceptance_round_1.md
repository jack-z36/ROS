# deploy_006 Acceptance — Round 1

## 1. 验收轮次

Round 1 (of max 3).

## 2. 读取的文件

| 文件 | 用途 |
|------|------|
| `AGENTS.md` | 全局路由入口，确认任务类型为 L3 微元任务执行 |
| `skills/stage4-l3-orchestrator/SKILL.md` | Stage4 L3 编排器技能 — 验收子 agent 规则、结论格式 |
| `DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_006_验收卡片.md` | **验收卡片（本卡片）** — 验收标准、命令、静态检查清单 |
| `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_006_command重构与删BridgeMux.md` | L3 任务文件 — 目标、允许/禁止修改、执行摘要、成功标准 |
| `src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py` | 被修改文件之一 — 当前代码状态 |
| `src/model_deploy/pi05/common/src/pi05/common/ros/topics.py` | 被修改文件之二 — 当前代码状态 |
| `src/model_deploy/pi05/deploy/config/deploy.yaml` | 实测 YAML 加载 — 验证新旧 schema 兼容性 |
| `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/` | 验收日志目录 — 确认路径正确 |
| Git diff (`HEAD~1`) | 检查执行 agent 实际修改范围 |

## 3. 执行的命令与静态检查项

### 3.1 本地验收命令（来自卡片 §35-56）

```bash
python3 -c "
schema = open('src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py', encoding='utf-8').read()
topics = open('src/model_deploy/pi05/common/src/pi05/common/ros/topics.py', encoding='utf-8').read()
assert 'policy_action' in schema and 'policy_action' in topics
for cls in ['BridgeTopicsConfig','MuxTopicsConfig','BridgeConfig','MuxConfig']:
    assert f'class {cls}' not in schema, f'{cls} should be removed'
for fn in ['_bridge_topics','_mux_topics','_mux_config']:
    assert f'def {fn}' not in schema, f'{fn} should be removed'
for f in ['left_arm_joint_target','left_hand_target']:
    assert f not in schema or 'command' not in schema.split(f)[0][-50:], f'old command field {f} in CommandTopicsConfig'
print('deploy_006 验收通过: command收敛policy_action, Bridge/Mux已删')
"
```

**结果：✅ PASS** — 输出 `deploy_006 验收通过: command收敛policy_action, Bridge/Mux已删`

### 3.2 Import / dataclass 行为验证

```bash
PYTHONPATH="src/model_deploy/pi05/common/src:src/model_deploy/pi05/deploy/src:$PYTHONPATH" python3 -c "
from pi05.common.ros.topics import Pi05CommandTopics
from pi05.deploy.config.schema import (
    CommandTopicsConfig, TopicsConfig, DeployConfig,
    BundleConfig, RuntimeConfig, ImageConfig, SafetyConfig
)
cmd = Pi05CommandTopics.with_namespace('/pi05')
assert cmd.policy_action == '/pi05/policy_action'
ctc = CommandTopicsConfig(policy_action='...', status='...', metrics='...')
assert not hasattr(ctc, 'left_arm_joint_target')
tc = TopicsConfig(...)
assert not hasattr(tc, 'bridge_output') and not hasattr(tc, 'mux')
dc = DeployConfig(...)
assert not hasattr(dc, 'bridge') and not hasattr(dc, 'mux')
# frozen preserved
try: ctc.policy_action = '/override'; assert False
except Exception: pass
# old classes not importable
try: from pi05.deploy.config.schema import BridgeTopicsConfig; assert False
except ImportError: pass
"
```

**结果：✅ PASS** — 全部断言通过

### 3.3 端到端 YAML 加载验证

```bash
PYTHONPATH="src/model_deploy/pi05/common/src:src/model_deploy/pi05/deploy/src:$PYTHONPATH" python3 -c "
from pi05.deploy.config.schema import load_deploy_config
config = load_deploy_config('src/model_deploy/pi05/deploy/config/deploy.yaml')
assert not hasattr(config.topics, 'bridge_output')
assert not hasattr(config.topics, 'mux')
assert not hasattr(config, 'bridge')
assert not hasattr(config, 'mux')
"
```

**结果：✅ PASS** — 新 schema 正确忽略 deploy.yaml 中的旧 bridge/mux 键，加载成功

### 3.4 静态评审清单

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 任务文件身份、dispatch task_id、验收卡片 task_id 一致 | ✅ PASS | 三者均为 `deploy_006` |
| 2 | 执行摘要存在，列出修改文件、命令、结果、未验证项 | ✅ PASS | L3 文件 §16 执行摘要完整 |
| 3 | 修改范围不超出 L3 允许修改边界 | ✅ PASS | 仅改 `schema.py`（command + 删 Bridge/Mux）和 `topics.py`（Pi05CommandTopics），在允许列表内 |
| 4 | 禁止修改项没有被触碰 | ✅ PASS | `ObservationTopicsConfig`/`_observation_topics` 未改（仅 import 行增加了 `DEFAULT_NAMESPACE`，不涉及类本身）；`RuntimeConfig`/`SafetyConfig` 未改；bridge_node/mux_node 源文件存在 |
| 5 | 当前代码路径仍使用 `src/model_deploy/pi05/...` | ✅ PASS | 路径正确 |
| 6 | 无硬件项没有被写成真机通过 | ✅ PASS | 无硬件声明 |

## 4. 观察到的通过 / 失败现象

### 通过项

1. **AST 断言通过** — `policy_action` 同时在 schema.py 和 topics.py 中存在；`BridgeTopicsConfig`/`MuxTopicsConfig`/`BridgeConfig`/`MuxConfig` 四个类已删除；`_bridge_topics`/`_mux_topics`/`_mux_config` 三个函数已删除；旧 command 字段 `left_arm_joint_target`/`left_hand_target` 不在 `CommandTopicsConfig` 中。

2. **Import 与 dataclass 行为通过** — `Pi05CommandTopics` 仅含 `policy_action`/`status`/`metrics`；`CommandTopicsConfig` 同理；`TopicsConfig` 无 `bridge_output`/`mux`；`DeployConfig` 无 `bridge`/`mux`；frozen 约束保留；旧 Bridge/Mux 类不可导入。

3. **端到端 YAML 加载通过** — 现行 deploy.yaml（含旧 bridge/mux 键）仍能被新 schema 加载，旧键被忽略存入 `raw`，不破坏启动流程。

4. **静态审查通过** — 身份一致；执行摘要完整；修改范围合规；禁止修改项未触碰；路径正确；无硬件冒用。

### 未验证项（按 L3 允许范围暂不验证）

- deploy.yaml 旧 bridge/mux 键更新 → deploy_008 处理。
- deploy_node `_create_subscriptions` 适配 → L2-03 处理。
- bridge_node/mux_node 源文件删除 → 按 L3 约束保留（git 回滚路径）。
- RuntimeConfig/SafetyConfig 的 topic 字段调整 → deploy_007 处理。
- 真机行为 → 本 L3 无真机影响（robot_risk: none）。

## 5. 最终结论

```
PASS_LOCAL
```

## 6. 结论依据

执行 agent 完成了 deploy_006 L3 的唯一目标：

1. **command topic 收敛** — `CommandTopicsConfig` 四路关节/手部目标 → 单路 `policy_action`；`Pi05CommandTopics` 同步；`_command_topics` 解析更新。
2. **Bridge/Mux config 删除** — 四个类（`BridgeTopicsConfig`/`MuxTopicsConfig`/`BridgeConfig`/`MuxConfig`）、三个解析函数（`_bridge_topics`/`_mux_topics`/`_mux_config`）全部删除；`TopicsConfig`/`DeployConfig` 对应字段删除；`_deploy_from_mapping` 中 bridge_raw/mux_raw 提取和构造参数已删除。
3. **三组自动化验收全部通过** — AST 断言、import/dataclass 行为、端到端 YAML 加载。
4. **静态评审全部通过** — 禁止修改项未被触碰，桥/mux 源文件保留。

无回修项。可按 dispatch 顺序进入下一 L3。

---

验收 agent: stage4-l3-acceptance
时间: 2026-06-20 16:00 CST
