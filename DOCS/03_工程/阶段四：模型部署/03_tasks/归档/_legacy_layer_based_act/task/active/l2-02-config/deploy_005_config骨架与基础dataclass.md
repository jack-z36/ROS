# L3 微元改造任务：新建 ACT config schema 骨架与基础 dataclass

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-02 ACT Config 层
来源 ACT Delta：A4（config schema，维度 16/16、`/act/*` topic、bundle、safety）
L3 编号：deploy_005
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_005_config骨架与基础dataclass.md`
改造类型：behavior-change（从零新建，结构参考同事源码）
真机风险等级：none
L2 Git 分支：`feat/model_deploy/l2-02-config`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/`
对应 L2 运行验收场景：S2（Config 层加载与校验）
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_005_验收卡片.md`
验收模式：direct-local
辅助验收模式：无
本地验收是否必须：true
验收反馈目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs/`

> [!warning] 产物落点约束
> 本 L3 产出的所有文件必须落到 `ACT代码树分层与产物落点约束.md` 规定的唯一位置。第 9 节声明每个产物的落点路径。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_005
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-config/deploy_005_config骨架与基础dataclass.md
  group: l2-02-config
  branch: feat/model_deploy/l2-02-config
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config
  acceptance_scenarios: [S2]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-02-config/deploy_005_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-config/logs
  wave: 1
  parallel_group: l2-02-config-w1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: []
  blocks: [deploy_006, deploy_007, deploy_008]
  conflict_scope:
    files:
      - src/model_deploy/act/config/schema.py
      - src/model_deploy/act/config/__init__.py
    modules:
      - act.config.schema
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 src/model_deploy/act/config/schema.py 的骨架：DeployConfigError + 辅助函数集（_str/_choice/_bool/_float 等）
+ 基础 dataclass（BundleConfig、ImageConfig、RuntimeConfig 框架）+ DeployConfig 顶层容器 + load_deploy_config。
此时尚不含 TopicsConfig/SafetyConfig 的具体字段（deploy_006/007 填充），但 DeployConfig 结构和加载链路打通。
辅助函数（约100行）从同事源码直接复用，零改动。
```

## 4. 来源契约

| 字段 | 内容 |
|---|---|
| Delta 编号 | A4 |
| AS-IS 契约 | 无 ACT config。Pi0.5 的 `deploy/config/schema.py`（561行）含完整 DeployConfig，但维度 14/26、topic `/pi05_vla/*`、含 Bridge/Mux。 |
| TO-BE 契约 | 新建 ACT config schema，结构复用同事框架。本 L3 先建骨架与基础 dataclass。 |

所属 L2：[[L2-02-ACT Config层]]

## 5. 现有程序盘点

| 现有对象 | 路径 | 行数 | 已有能力 | 与目标的差距 | 复用方式 |
|---|---|---|---|---|---|
| `DeployConfigError` | `pi05_old/.../config/schema.py:18-19` | 2 | ValueError 子类 | 通用，零改动 | **直接复用** |
| 辅助函数 `_str/_optional_str/_choice/_bool/_int_value/_float/_positive_int/_non_negative_int/_positive_float/_float_list/_mapping/_required_mapping/_path` | `:465-561` | ~97 | 类型安全的 YAML 取值 | 通用，零改动 | **直接复用** |
| `BundleConfig` | `:22-30` | 9 | bundle_dir + resolved_bundle_dir | 通用 | **直接复用** |
| `ImageConfig` | `:230-236` | 7 | image_size/resize_mode/transport | 通用（224 默认值可保留） | **直接复用** |
| `RuntimeConfig` | `:33-91` | 59 | mode/device/hz/chunk/fallback 等调度参数 | 默认值 `action_dim=14/state_dim=26` 需改 16/16；其余通用 | **结构复用**（本 L3 先搬框架，007 改默认值与 mode 校验） |
| `DeployConfig` + `from_mapping` + `load_deploy_config` + `_deploy_from_mapping` | `:239-264` | 26 | 顶层容器 + YAML 加载 | 结构通用；引用的子 config 待 006/007 填充 | **结构复用** |

## 6. 真实改造边界

### 本次允许做

- 新建 `src/model_deploy/act/config/__init__.py`（re-export）。
- 新建 `src/model_deploy/act/config/schema.py`：
  - `DeployConfigError`（直接复用）。
  - 全部辅助函数（直接复用，约 97 行）。
  - `BundleConfig`（直接复用）。
  - `ImageConfig`（直接复用）。
  - `RuntimeConfig` 框架（搬同事的，但 `action_dim/state_dim` 暂留，007 统一改；mode 三档枚举暂保留同事的 dry-run/shadow-run/safe-run）。
  - `DeployConfig` 顶层 dataclass：本 L3 暂用占位子 config（TopicsConfig/SafetyConfig 在 006/007 加入前，可先注释或用占位）。
  - `load_deploy_config(path)` + `DeployConfig.from_mapping`。
- 新建 `src/model_deploy/act/config_files/` 目录（空，008 填 deploy.yaml）。
- 新建 `act/tests/config/__init__.py` + `act/tests/config/test_schema_base.py`（基础加载单测）。

### 本次不做

- 不写 TopicsConfig 的具体字段（deploy_006）。
- 不写 SafetyConfig 的 TCP 检查项（deploy_007）。
- 不改 RuntimeConfig 的 action_dim/state_dim 默认值（deploy_007 统一改，避免本 L3 与 007 冲突）。
- 不写 deploy.yaml 实例（deploy_008）。

### 明确禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/**`（L2-01 产物）

## 7. 实施步骤

1. 新建目录 `act/config/`、`act/config_files/`、`act/tests/config/`。
2. 新建 `act/config/schema.py`：
   - docstring：ACT 部署配置，16D 维度，`/act/*` namespace。
   - `DeployConfigError(ValueError)`。
   - 辅助函数段（从同事 `:465-561` 直接复用，仅去掉对 `Pi05ObservationTopics` 的 import 依赖）。
   - `BundleConfig`（直接复用 `:22-30`）。
   - `ImageConfig`（直接复用 `:230-236`）。
   - `RuntimeConfig`（搬 `:33-91`，保留全部字段和 `__post_init__` 校验；action_dim/state_dim 暂保留原值，007 改）。
   - `DeployConfig` 顶层（搬 `:239-254`，topics/safety 字段先用占位 `dict` 或注释，006/007 替换为正式 dataclass）。
   - `load_deploy_config`（直接复用 `:257-264`）。
3. 处理 `_deploy_from_mapping`：本 L3 暂时简化（只解析 bundle/runtime/image，topics/safety 跳过或用空 dict 占位），006/007 补全。**写明 TODO 注释**标注待填充点。
4. 新建 `act/config/__init__.py`：re-export `DeployConfig`/`load_deploy_config`/`DeployConfigError`。
5. 新建 `act/tests/config/test_schema_base.py`：加载含 bundle+runtime 的最小合法 YAML 成功；缺 bundle 报错；runtime 非法 hz 报错。
6. 运行 pytest。

## 8. 验证方式

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/config/test_schema_base.py -v
```

| 层级 | 是否需要 | 通过标准 |
|---|---|---|
| unit | 是 | test_schema_base.py PASSED |
| 其余 | 否 | — |

L2 贡献：Config 骨架与加载链路打通。

## 9. 允许修改

| 产物 | 落点路径 | 所属层 |
|---|---|---|
| config schema 源码 | `src/model_deploy/act/config/schema.py` | config |
| config 包标记 | `src/model_deploy/act/config/__init__.py` | config |
| config_files 目录 | `src/model_deploy/act/config_files/`（空，008 填） | config_files |
| 单测 | `src/model_deploy/act/tests/config/test_schema_base.py` | tests/config |

## 10. 禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/**`

## 11. 必读上下文

- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-02-ACT Config层.md`
- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py`（AS-IS 参考，561行）
- `DOCS/02_约束/编程执行/Agent编程执行原则.md`
- `DOCS/02_约束/编程执行/架构边界与机械约束原则.md`
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

## 12. 执行要求

- 身份校验：分支 `feat/model_deploy/l2-02-config`。
- 依赖校验：L2-01（Types）已合入或可用（RuntimeConfig 引用 ACTION_DIM/STATE_DIM 在 007 做）。
- TDD：先写最小加载单测。
- 落点校验：产物路径与第 9 节一致。

## 13. 成功标准

- [ ] `act/config/schema.py` 存在，含 `DeployConfigError` + 全部辅助函数 + `BundleConfig` + `ImageConfig` + `RuntimeConfig` + `DeployConfig` + `load_deploy_config`。
- [ ] 辅助函数（~97行）与同事源码逻辑一致。
- [ ] `load_deploy_config` 能加载含 bundle+runtime 的最小 YAML。
- [ ] 缺 bundle 或非法 hz 时抛 `DeployConfigError`。
- [ ] `test_schema_base.py` PASSED。
- [ ] 未修改 pi05/third_party/pi05_old/types。

## 14. 回滚方式

删除 `src/model_deploy/act/config/`。

## 15. 完成后交接

（执行 sub-agent 完成后填写）
