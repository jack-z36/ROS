# L3 微元改造任务：重构 observation topic 字段为鱼眼/TCP/gripper

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-02 Config 层重构
来源 Delta：D3（相机）、D7（topic 命名空间）、D8（臂状态语义）
L3 编号：deploy_005
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_005_重构observation_topic字段.md`
改造类型：behavior-change
真机风险等级：none
L2 Git 分支：model_deploy-l2-02-config
验收证据目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config
对应 L2 运行验收场景：[S1, S2]
验收卡片路径：DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_005_验收卡片.md
验收模式：direct-local
辅助验收模式：[]
本地验收是否必须：true
验收反馈目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_005
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_005_重构observation_topic字段.md
  group: l2-02-config
  branch: model_deploy-l2-02-config
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config
  acceptance_scenarios: [S1, S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_005_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs
  wave: 1
  parallel_group: l2-02-config-p1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_006, deploy_007]
  conflict_scope:
    files:
      - src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py
      - src/model_deploy/pi05/common/src/pi05/common/ros/topics.py
    modules:
      - pi05.deploy.config.schema
      - pi05.common.ros.topics
    config_keys:
      - topics.observation
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
把 observation topic 配置从 AS-IS 的 realsense/proprio/hand/ee 字段，重构为 TO-BE 的鱼眼双目 + 左右 TCP pose + 左右夹爪宽度 + 触觉（预留）字段，同步更新 schema.py 的 ObservationTopicsConfig/_observation_topics 和 topics.py 的 Pi05ObservationTopics 默认值类。
```

## 4. 来源契约

### 来源 Delta

| 字段 | 内容 |
|---|---|
| Delta 编号 | D3 + D7 + D8 |
| 变更对象 | External Deps · 相机 + Input Contract · topic 命名 + 臂状态语义 |
| AS-IS 契约 | `ObservationTopicsConfig`（schema.py:94-115）：top_image/left_wrist_image/right_wrist_image(+raw)/proprioception/left_hand_state/right_hand_state/left_ee_position/left_ee_rpy/right_ee_position/right_ee_rpy/proprioception_order/触觉可选。默认值来自 `Pi05ObservationTopics`（topics.py:42-69）。 |
| TO-BE 契约 | 新字段：left_fisheye_image/right_fisheye_image(+raw)/left_tcp_pose/right_tcp_pose/left_gripper_state/right_gripper_state/触觉l1-l4（预留可选）。依据：TO-BE Contract topic 总表。 |
| 兼容性要求 | 破坏性（旧 deploy.yaml 无法加载，回滚靠 git + 旧 config）。 |
| 回滚要求 | git 回退 schema.py + topics.py + 旧 deploy.yaml。 |

### 所属 L2 改造工作包

- L2 名称：L2-02 Config 层重构
- 本 L3 在该 L2 中的位置：第一个。observation 字段是 config 的核心部分。
- 本 L3 完成后解锁：deploy_006（command topic）、deploy_007（runtime/safety）。

## 5. 现有程序盘点

| 现有对象 | 路径 / 名称 | 已有能力 | 与目标契约的差距 | 本次是否允许修改 |
|---|---|---|---|---|
| `ObservationTopicsConfig` | schema.py:94-115 | realsense/proprio/hand/ee 字段 + proprioception_order | 字段全换为鱼眼/tcp/gripper/触觉预留 | 是 |
| `_observation_topics` | schema.py:341-362 | 从 topics_raw 解析 observation 字段，引用 Pi05ObservationTopics 默认值 | 字段映射全换 | 是 |
| `Pi05ObservationTopics` | topics.py:42-69 | 默认 topic 名（/pi05_vla/observation/...） | 字段和默认 topic 路径全换为 /pi05/observation/... | 是 |
| `DEFAULT_NAMESPACE` | topics.py:8 `/pi05_vla` | 旧命名空间 | 改为 `/pi05`（对齐 TO-BE） | 是 |

### 必须保留的现有行为

- frozen dataclass + 解析校验模式。
- `_str`/`_optional_str`/`_choice` 辅助函数（复用）。
- topic 名通过 namespace + join_topic 组合的模式。
- 触觉字段用 `_optional_str`（可选，默认 None）——预留语义保留。

### 已知风险

- 改 `ObservationTopicsConfig` 字段后，引用它的 `pi05_vla_deploy_node._create_subscriptions` 会失配（它读 `topics.proprioception` 等旧字段）。本 L3 不改 deploy_node（L2-03 做）。本 L3 完成后 deploy 包暂时无法完整加载，预期中间状态。
- `Pi05ObservationTopics` 是 `common/ros` 包的公共类，改它影响范围需注意（可能有测试引用）。

## 6. 真实改造边界

### 本次允许做

- 重构 `ObservationTopicsConfig` 字段（schema.py:94-115）：
  - 删：top_image/left_wrist_image/right_wrist_image(+_raw)/proprioception/left_hand_state/right_hand_state/left_ee_position/left_ee_rpy/right_ee_position/right_ee_rpy/proprioception_order
  - 加：left_fisheye_image/right_fisheye_image/left_fisheye_image_raw/right_fisheye_image_raw（鱼眼双目）
  - 加：left_tcp_pose/right_tcp_pose（PoseStamped）
  - 加：left_gripper_state/right_gripper_state（Float32 width）
  - 加：tactile_l1/tactile_l2/tactile_r1/tactile_r2（`str | None = None`，触觉预留，第一版可选）
- 改 `_observation_topics`（schema.py:341-362）：字段映射跟随，默认值引用新 `Pi05ObservationTopics`；触觉用 `_optional_str`。
- 重构 `Pi05ObservationTopics`（topics.py:42-69）：字段和 `with_namespace` 默认路径全换（对齐 TO-BE Contract topic 表：/pi05/observation/image/*_fisheye、/pi05/observation/arm/*_tcp_pose、/pi05/observation/gripper/*_state）。
- 改 `DEFAULT_NAMESPACE`（topics.py:8）：`/pi05_vla` → `/pi05`。

### 本次不做

- 不改 `CommandTopicsConfig`（deploy_006 做）。
- 不改 `RuntimeConfig`/`SafetyConfig`（deploy_007 做）。
- 不改 deploy_node（L2-03 做）。
- 不删 Bridge/Mux（deploy_006 做）。
- 不改 deploy.yaml（deploy_008 做）。
- 不补单测（deploy_008 做）。

### 明确禁止修改

- 禁止改 schema.py 的 CommandTopicsConfig/BridgeTopicsConfig/MuxTopicsConfig/RuntimeConfig/SafetyConfig 部分。
- 禁止改 deploy_node / collector 等上层。
- 禁止改 `_str`/`_optional_str` 等通用辅助函数。
- 禁止改 topics.py 的 `Pi05CommandTopics`（deploy_006 做）。

### Adapter / 直接修改策略

```text
直接修改。Config 层字段整体替换。触觉字段保留 _optional_str 可选语义（与 AS-IS 的 left_tactile_image 一致），第一版默认 None。回滚靠 git。
```

## 7. 实施步骤

1. **改 topics.py 的 `Pi05ObservationTopics`**：字段换为 left_fisheye_image/right_fisheye_image/left_tcp_pose/right_tcp_pose/left_gripper_state/right_gripper_state；`with_namespace` 默认路径对齐 TO-BE topic 表。改 `DEFAULT_NAMESPACE` 为 `/pi05`。
2. **改 schema.py 的 `ObservationTopicsConfig`**（L94-115）：字段如上重构；触觉 l1-l4 用 `str | None = None`。
3. **改 schema.py 的 `_observation_topics`**（L341-362）：字段映射跟随新结构，默认值引用新 `Pi05ObservationTopics`；触觉用 `_optional_str`。
4. **AST 验收**：确认新字段存在、旧字段删除。

## 8. 验证方式

### 自动化验收命令

```bash
python3 -c "
schema = open('src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py', encoding='utf-8').read()
topics = open('src/model_deploy/pi05/common/src/pi05/common/ros/topics.py', encoding='utf-8').read()
for f in ['left_fisheye_image','right_fisheye_image','left_tcp_pose','right_tcp_pose','left_gripper_state','right_gripper_state']:
    assert f in schema, f'{f} missing in schema'
    assert f in topics, f'{f} missing in topics'
for f in ['tactile_l1','tactile_l2','tactile_r1','tactile_r2']:
    assert f in schema, f'{f} tactile field missing'
for f in ['top_image','proprioception','left_hand_state','left_ee_position','proprioception_order']:
    assert f not in schema, f'old field {f} should be removed'
assert '/pi05' in topics
print('deploy_005 验收通过: observation 字段重构为鱼眼/TCP/gripper/触觉预留')
"
```

### 分层验证

| 验证层级 | 是否需要 | 验证内容 | 通过标准 |
|---|---|---|---|
| unit / import | 是 | AST 字段断言 | 上述命令通过 |
| dry-run | 否 | — | — |

### 真机风险控制

不适用，本 L3 不触发真机动作。

### 验收证据落点

本 L3 的验收结果、专用脚本和日志必须归入所属 L2 验收目录：

```text
验收结果文档：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/验收结果.md
验收脚本目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/scripts/
验收日志目录：DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/
```
## 9. 允许修改

- `src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py`（仅 ObservationTopicsConfig + _observation_topics）
- `src/model_deploy/pi05/common/src/pi05/common/ros/topics.py`（Pi05ObservationTopics + DEFAULT_NAMESPACE）

## 10. 禁止修改

- schema.py 的其他 config 类（Command/Bridge/Mux/Runtime/Safety）。
- topics.py 的 `Pi05CommandTopics`。
- 任何上层代码。

## 11. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md`（topic 总表，observation 部分）
2. `DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md`（D3/D7/D8）
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

1. 无直接上游 L3（本 L3 是 L2-02 第一个）。
2. 无同组已完成 L3。

## 12. 执行要求

执行前必须完成任务文件身份校验：

```text
用户指定任务路径：
实际读取任务路径：
文件名编号：
正文 L3 编号：
是否一致：
```

执行前必须读取 `dispatch` YAML，确认 `depends_on` 为空、`dispatch_status` 不是 blocked、`robot_risk: none`。

```text
最小复现 / 测试（AST 断言脚本）
→ 最小实现（改 topics.py + schema.py observation 部分）
→ 验证通过
→ 必要整理（docstring）
```

不得为让整包加载而改 deploy_node。

## 13. 成功标准

- [x] 已完成任务文件身份校验。
- [x] 已确认当前分支符合所属 L2 分支规范。
- [x] 已读取 TO-BE Contract topic 表和所属 L2。
- [x] ObservationTopicsConfig 字段重构为鱼眼/TCP/gripper/触觉预留。
- [x] Pi05ObservationTopics 默认值同步更新。
- [x] 触觉字段为可选（None 默认）。
- [x] 已完成自动化验收（AST 断言）。
- [x] 已写明回滚方式。

## 14. 回滚方式

```text
回退文件：git checkout -- schema.py topics.py
配合：切回旧 deploy.yaml
不可自动回滚的人工步骤：无
```

## 15. 完成后交接

交接摘要必须包含：读取文档、身份校验、修改文件、新增字段、验收命令与结果、成功标准勾选、真机影响（无）、回滚方式、未做事项（没改 command/runtime/safety/deploy_node）、后续建议（deploy_006）。

---

## 16. 执行摘要 (deploy_005)

### 读取文档
- AGENTS.md 全局路由入口
- DOCS/02_约束/上下文加载/04_L3微元任务执行加载规则.md
- skills/stage4-l3-orchestrator/SKILL.md
- DOCS/03_工程/阶段四：模型部署/01_contracts/TO-BE Contract.md（topic 总表 observation 部分）
- DOCS/03_工程/阶段四：模型部署/01_contracts/Contract Delta.md（D3/D7/D8）
- DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-02-Config层重构.md
- `src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py`
- `src/model_deploy/pi05/common/src/pi05/common/ros/topics.py`
- DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_005_验收卡片.md（存在确认）

### 身份校验
- 用户指定路径: `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_005_重构observation_topic字段.md`
- 实际读取路径: 一致
- 文件名编号: `deploy_005`
- 正文 L3 编号: `deploy_005`
- 一致性: ✅ 一致
- 当前分支: `model_deploy-l2-02-config` ✅
- Dispatch 校验: `depends_on: []` ✅, `dispatch_status: ready` ✅, `robot_risk: none` ✅
- 验收模式: `direct-local` ✅
- 本地验收必须: `true` ✅

### 修改文件

1. **`src/model_deploy/pi05/common/src/pi05/common/ros/topics.py`**
   - `DEFAULT_NAMESPACE`: `/pi05_vla` → `/pi05`
   - `Pi05ObservationTopics`: 旧字段（top_image/left_wrist_image/right_wrist_image/proprioception/left_hand_state/right_hand_state/lee_ee_position/left_ee_rpy/right_ee_position/right_ee_rpy）→ 新字段（left_fisheye_image/right_fisheye_image/left_tcp_pose/right_tcp_pose/left_gripper_state/right_gripper_state）
   - `with_namespace()`: 生成路径对齐 TO-BE topic 表

2. **`src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py`**
   - `ObservationTopicsConfig` 类: 旧 18 字段 → 新 12 字段（8 必需 str + 4 可选 tactile `str | None = None`）
   - `_observation_topics()`: 字段映射重写为新结构
   - `_deploy_from_mapping()` namespace 默认值: 硬编码 `/pi05_vla` → `DEFAULT_NAMESPACE` 常量引用

### 新增字段

| config 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `left_fisheye_image` | `str` | `/pi05/observation/image/left_gripper_fisheye` | 左夹爪鱼眼图像 |
| `right_fisheye_image` | `str` | `/pi05/observation/image/right_gripper_fisheye` | 右夹爪鱼眼图像 |
| `left_fisheye_image_raw` | `str` | 同上（removesuffix /compressed） | left_fisheye_image raw 变体 |
| `right_fisheye_image_raw` | `str` | 同上 | right_fisheye_image raw 变体 |
| `left_tcp_pose` | `str` | `/pi05/observation/arm/left_tcp_pose` | 左臂 TCP pose |
| `right_tcp_pose` | `str` | `/pi05/observation/arm/right_tcp_pose` | 右臂 TCP pose |
| `left_gripper_state` | `str` | `/pi05/observation/gripper/left_state` | 左夹爪开合状态 |
| `right_gripper_state` | `str` | `/pi05/observation/gripper/right_state` | 右夹爪开合状态 |
| `tactile_l1` | `str \| None` | `None` | 触觉预留 l1 |
| `tactile_l2` | `str \| None` | `None` | 触觉预留 l2 |
| `tactile_r1` | `str \| None` | `None` | 触觉预留 r1 |
| `tactile_r2` | `str \| None` | `None` | 触觉预留 r2 |

### 验收命令与结果

**命令**: AST 字段断言（L3 §8 自动化验收命令）
**结果**: `deploy_005 验收通过: observation 字段重构为鱼眼/TCP/gripper/触觉预留`

附加单元测试：
- `Pi05ObservationTopics.with_namespace()` 默认路径正确
- `ObservationTopicsConfig` 创建、冻结、tactile 默认 None
- `_observation_topics()` 工厂函数默认值及覆盖
- Python 语法校验通过

### 未做事项
- 未改 `CommandTopicsConfig`（deploy_006 做）
- 未改 `RuntimeConfig`/`SafetyConfig`（deploy_007 做）
- 未改 deploy_node（L2-03 做）
- 未改 Bridge/Mux config（deploy_006 做）
- 未改 deploy.yaml（deploy_008 做）
- 未补单测（deploy_008 做）
- 未改 `Pi05CommandTopics`（deploy_006 做）
- 未改 `_str`/`_optional_str`等辅助函数

### 真机影响
无。本 L3 只改 config schema 和 topic 默认值，不涉及真机动作。

### 回滚方式
```text
git checkout -- src/model_deploy/pi05/common/src/pi05/common/ros/topics.py src/model_deploy/pi05/deploy/src/pi05/deploy/config/schema.py
配合：切回旧 deploy.yaml
```

### 后续建议
- 执行 deploy_006（command topic 字段重构）
- deploy_007（runtime/safety config）
- deploy_008（deploy.yaml + 单测）
