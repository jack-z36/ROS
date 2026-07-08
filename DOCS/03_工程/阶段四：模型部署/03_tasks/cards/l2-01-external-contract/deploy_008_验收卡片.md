---
task_id: deploy_008
task_name: DeployConfig核心schema与校验器
l2: l2-01-external-contract
acceptance_mode: direct-local
acceptance_round_limit: 3
local_acceptance_required: true
dispatch_status: ready
acceptance_scenarios: [S1, S2, S5]
---

# deploy_008 验收卡片 — DeployConfig 核心 schema 与校验器

## 1. 验收元信息

| 字段 | 值 |
|------|-----|
| task_id | deploy_008 |
| task_name | DeployConfig 核心 schema 与校验器 |
| L2 | l2-01-external-contract |
| 验收模式 | direct-local |
| 真机风险 | none |
| acceptance_round_limit | 3 |
| local_acceptance_required | true |
| acceptance_scenarios | S1, S2, S5 |
| 验收人 | agent |
| 产出文件 | src/model_deploy/act/config/schema.py, src/model_deploy/act/config_files/deploy.yaml, src/model_deploy/act/tests/config/test_schema.py |
| 验收反馈目录 | DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs |

## 2. PASS_LOCAL 条件

> [!warning] 以下全部条件必须满足方可 PASS_LOCAL。任一条件不满足则 FAIL_LOCAL，进入下一轮修复。

### 2.1 文件存在性

- [ ] `src/model_deploy/act/config/schema.py` 存在
- [ ] `src/model_deploy/act/config_files/deploy.yaml` 存在
- [ ] `src/model_deploy/act/tests/config/test_schema.py` 存在

### 2.2 异常与 dataclass 定义

- [ ] `DeployConfigError(ValueError)` 已定义
- [ ] `BundleConfig` 为 `@dataclass(frozen=True)`
- [ ] `RuntimeConfig` 为 `@dataclass(frozen=True)`
- [ ] `SafetyConfig` 为 `@dataclass(frozen=True)`
- [ ] `TopicsConfig` 为 `@dataclass(frozen=True)`
- [ ] `ImageConfig` 为 `@dataclass(frozen=True)`
- [ ] `DeployConfig` 为 `@dataclass(frozen=True)`

### 2.3 移除项检查（bridge/mux）

- [ ] schema.py 中**无** `BridgeConfig`
- [ ] schema.py 中**无** `MuxConfig`
- [ ] schema.py 中**无** `BridgeTopicsConfig`
- [ ] schema.py 中**无** `MuxTopicsConfig`
- [ ] `TopicsConfig` **无** `bridge_output` 字段
- [ ] `TopicsConfig` **无** `mux` 字段
- [ ] `DeployConfig` **无** `bridge` 字段
- [ ] `DeployConfig` **无** `mux` 字段

### 2.4 平滑字段移除检查（S5）

- [ ] `RuntimeConfig` **无** `blend_steps` 字段
- [ ] schema.py 中**无** `blend_steps`、`smoothstep`、`cross_chunk`、`rtc_alignment`、`action_smoothing` 任何匹配
- [ ] deploy.yaml 中**无**上述平滑字段任何匹配

### 2.5 维度检查

- [ ] `RuntimeConfig.state_dim` 默认值为 16（非 26）
- [ ] `RuntimeConfig.action_dim` 默认值为 16（非 14）
- [ ] deploy.yaml 中 `state_dim: 16`
- [ ] deploy.yaml 中 `action_dim: 16`

### 2.6 namespace 检查

- [ ] deploy.yaml 中 `topics.namespace` 为 `/act`（非 `/pi05_vla`）
- [ ] schema.py 中**无** `pi05_vla` 匹配

### 2.7 校验器检查

- [ ] typed validators 存在：`_str`、`_choice`、`_bool`、`_positive_int`、`_positive_float`、`_non_negative_int`、`_float`、`_optional_str`、`_required_mapping`、`_mapping`、`_path`、`_int_value`、`_float_list`
- [ ] 各 validator 校验失败时抛出 `DeployConfigError`
- [ ] 错误消息包含 key 名称

### 2.8 __post_init__ 校验检查

- [ ] `RuntimeConfig.__post_init__` 校验 `control_hz > 0`
- [ ] `RuntimeConfig.__post_init__` 校验 `inference_hz > 0`
- [ ] `RuntimeConfig.__post_init__` 校验 `execute_horizon <= chunk_size`
- [ ] `RuntimeConfig.__post_init__` 校验 `prefetch_steps <= execute_horizon`
- [ ] `RuntimeConfig.__post_init__` 校验 `max_action_age_sec > 0`
- [ ] `RuntimeConfig.__post_init__` 校验 `fallback_policy` 在枚举中
- [ ] `RuntimeConfig.__post_init__` **无** `blend_steps >= 0` 校验

### 2.9 from_mapping 组装检查

- [ ] `DeployConfig.from_mapping(cls, raw, *, base_dir)` classmethod 存在
- [ ] 组装顺序为：bundle → runtime → image → topics → safety → raw
- [ ] 组装中**无** bridge 步骤
- [ ] 组装中**无** mux 步骤
- [ ] `DeployConfig` 保留 `raw` 字段（原始 dict）

### 2.10 deploy.yaml 结构检查

- [ ] `bundle.bundle_dir` 存在（值为 null）
- [ ] `runtime` 段包含 mode, control_hz, inference_hz, chunk_size, execute_horizon, max_action_age_sec, fallback_policy, state_dim, action_dim
- [ ] `image` 段包含 image_size=224, resize_mode=resize_pad, transport=raw
- [ ] `topics` 段包含 namespace=/act, observation, command
- [ ] `safety` 段包含 max_tcp_delta_per_step=0.03, hand_min=300.0, hand_max=1000.0, quaternion_check=true
- [ ] deploy.yaml 中**无** bridge 段
- [ ] deploy.yaml 中**无** mux 段

### 2.11 功能测试（S1/S2）

- [ ] 合法 mapping 调用 `from_mapping` 成功构建 `DeployConfig`（S1）
- [ ] `state_dim=26` 调用 `from_mapping` 抛出 `DeployConfigError`（S2）
- [ ] `action_dim=14` 调用 `from_mapping` 抛出 `DeployConfigError`（S2）
- [ ] 非法 `control_hz <= 0` 抛出 `DeployConfigError`
- [ ] 非法 `mode` 抛出 `DeployConfigError`
- [ ] `execute_horizon > chunk_size` 抛出 `DeployConfigError`

### 2.12 pytest 通过

- [ ] `python3 -m pytest src/model_deploy/act/tests/config/test_schema.py -v` 全部通过

### 2.13 禁止修改范围检查

- [ ] `pi05/` 目录下文件未被修改
- [ ] `src/model_deploy/act/types/` 层未被修改
- [ ] `src/model_deploy/act/repo/` 层未被修改
- [ ] `src/model_deploy/act/service/` 层未被修改
- [ ] `src/model_deploy/act/runtime/` 层未被修改
- [ ] `src/model_deploy/act/ui/` 层未被修改

## 3. 验证命令

### 3.1 pytest 单元测试

```bash
python3 -m pytest src/model_deploy/act/tests/config/test_schema.py -v
```

预期输出：

```text
============================= test session starts =============================
collected 12 items

src/model_deploy/act/tests/config/test_schema.py ................     [100%]

============================= 12 passed =============================
```

### 3.2 平滑字段泄漏检查（S5）

```bash
rg -n 'blend_steps|smoothstep|cross_chunk|rtc_alignment|action_smoothing' src/model_deploy/act/config/schema.py src/model_deploy/act/config_files/deploy.yaml
```

预期输出（空 = 通过）：

```text
(无输出)
```

### 3.3 bridge/mux 残留检查

```bash
rg -n 'BridgeConfig|MuxConfig|BridgeTopicsConfig|MuxTopicsConfig|bridge_output' src/model_deploy/act/config/schema.py
```

预期输出（空 = 通过）：

```text
(无输出)
```

### 3.4 维度残留检查

```bash
rg -n 'state_dim.*26|action_dim.*14' src/model_deploy/act/config/schema.py src/model_deploy/act/config_files/deploy.yaml
```

预期输出（空 = 通过）：

```text
(无输出)
```

### 3.5 namespace 残留检查

```bash
rg -n 'pi05_vla' src/model_deploy/act/config/schema.py src/model_deploy/act/config_files/deploy.yaml
```

预期输出（空 = 通过）：

```text
(无输出)
```

### 3.6 frozen dataclass 检查

```bash
rg -n '@dataclass\(frozen=True\)' src/model_deploy/act/config/schema.py
```

预期输出（至少 6 个匹配）：

```text
6:    @dataclass(frozen=True)
20:    @dataclass(frozen=True)
50:    @dataclass(frozen=True)
80:    @dataclass(frozen=True)
95:    @dataclass(frozen=True)
120:    @dataclass(frozen=True)
```

### 3.7 禁止修改范围检查

```bash
git diff --name-only HEAD -- pi05/ src/model_deploy/act/types/ src/model_deploy/act/repo/ src/model_deploy/act/service/ src/model_deploy/act/runtime/ src/model_deploy/act/ui/
```

预期输出（空 = 通过）：

```text
(无输出)
```

### 3.8 deploy.yaml 结构验证

```bash
python3 -c "
import yaml
with open('src/model_deploy/act/config_files/deploy.yaml') as f:
    cfg = yaml.safe_load(f)
assert 'bundle' in cfg, 'missing bundle'
assert 'runtime' in cfg, 'missing runtime'
assert 'image' in cfg, 'missing image'
assert 'topics' in cfg, 'missing topics'
assert 'safety' in cfg, 'missing safety'
assert 'bridge' not in cfg, 'bridge should not exist'
assert 'mux' not in cfg, 'mux should not exist'
assert cfg['topics']['namespace'] == '/act', 'namespace must be /act'
assert cfg['runtime']['state_dim'] == 16, 'state_dim must be 16'
assert cfg['runtime']['action_dim'] == 16, 'action_dim must be 16'
print('deploy.yaml structure OK')
"
```

预期输出：

```text
deploy.yaml structure OK
```

## 4. 验收场景

### S1 — 合法配置载入

> [!warning] S1 验证 from_mapping 能从合法 mapping 成功构建 DeployConfig。

**验证步骤**：

```bash
python3 -m pytest src/model_deploy/act/tests/config/test_schema.py::test_valid_mapping_constructs -v
```

**合法 mapping 示例**：

```yaml
bundle:
  bundle_dir: /tmp/test_bundle
runtime:
  mode: dry-run
  control_hz: 30.0
  inference_hz: 10.0
  chunk_size: 30
  execute_horizon: 10
  max_action_age_sec: 0.45
  fallback_policy: hold_last_action
  state_dim: 16
  action_dim: 16
image:
  image_size: 224
  resize_mode: resize_pad
  transport: raw
topics:
  namespace: /act
  observation:
    arm_state: arm_state
  command:
    arm_command: arm_command
safety:
  max_tcp_delta_per_step: 0.03
  hand_min: 300.0
  hand_max: 1000.0
  quaternion_check: true
```

**预期结果**：

```text
PASSED — DeployConfig 成功构建，无异常
```

### S2 — 非法维度失败

> [!warning] S2 验证 state_dim/action_dim != 16 时 from_mapping 抛出 DeployConfigError。

**验证步骤**：

```bash
python3 -m pytest src/model_deploy/act/tests/config/test_schema.py::test_invalid_state_dim_raises src/model_deploy/act/tests/config/test_schema.py::test_invalid_action_dim_raises -v
```

**非法 mapping 示例（state_dim=26）**：

```yaml
runtime:
  state_dim: 26
  action_dim: 16
```

**非法 mapping 示例（action_dim=14）**：

```yaml
runtime:
  state_dim: 16
  action_dim: 14
```

**预期结果**：

```text
PASSED — DeployConfigError 被抛出
```

### S5 — 无平滑配置泄漏

> [!warning] S5 验证 deploy.yaml 和 schema.py 不含任何平滑相关字段。

**验证步骤**：

```bash
rg -n 'blend_steps|smoothstep|cross_chunk|rtc_alignment|action_smoothing' src/model_deploy/act/config/schema.py src/model_deploy/act/config_files/deploy.yaml
```

**预期结果**：

```text
(无输出 — 空输出表示无匹配，通过)
```

## 5. 反馈记录

> [!warning] 每轮验收结果记录于此。最多 3 轮，超过则 dispatch_status 改为 blocked。

### Round 1

| 字段 | 值 |
|------|-----|
| 验收时间 | |
| 结果 | |
| 失败条件 | |
| 失败原因 | |
| 修复指令 | |

### Round 2

| 字段 | 值 |
|------|-----|
| 验收时间 | |
| 结果 | |
| 失败条件 | |
| 失败原因 | |
| 修复指令 | |

### Round 3

| 字段 | 值 |
|------|-----|
| 验收时间 | |
| 结果 | |
| 失败条件 | |
| 失败原因 | |
| 修复指令 | |

## 6. 备注

### 6.1 验收流程

1. 执行第 3 节全部验证命令
2. 逐条检查第 2 节 PASS_LOCAL 条件
3. 全部满足 → PASS_LOCAL，记录到第 5 节 Round
4. 任一不满足 → FAIL_LOCAL，记录失败条件和原因，进入下一轮
5. 超过 3 轮 → dispatch_status 改为 blocked

### 6.2 与 deploy_009 的衔接

deploy_008 PASS_LOCAL 后，deploy_009 可启动。deploy_009 依赖本任务产出的：
- `DeployConfig` dataclass（含 raw 字段）
- `DeployConfig.from_mapping` classmethod
- `DeployConfigError` 异常
- 各子配置 dataclass 的 field 列表

### 6.3 常见失败模式

| 失败模式 | 原因 | 修复 |
|---------|------|------|
| rg 检查有 blend_steps 匹配 | 从 Pi0.5 复制时未清除 | 删除所有平滑字段 |
| state_dim=26 残留 | 从 Pi0.5 复制时未修改 | 改为 16 |
| BridgeConfig 残留 | 从 Pi0.5 复制时未删除 | 删除 bridge/mux 相关 dataclass |
| from_mapping 组装顺序错误 | 未按 bundle→runtime→image→topics→safety→raw | 调整组装顺序 |
| pytest 失败 | 校验逻辑不完整 | 补充 __post_init__ 校验分支 |
| pi05/ 被修改 | 误操作 | git checkout 恢复 |
