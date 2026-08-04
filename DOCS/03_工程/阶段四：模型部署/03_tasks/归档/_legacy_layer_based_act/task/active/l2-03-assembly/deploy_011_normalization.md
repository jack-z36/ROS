# L3 微元改造任务：新建 ACT normalization（ActionStateNormalizer mean-std）

## 1. 任务定位

阶段：阶段四：模型部署
L1：模型部署程序改造总目标
L2 改造工作包：L2-03 ACT 数据装配与模型加载
来源 ACT Delta：A5（normalization 部分复用）
L3 编号：deploy_011
当前任务文件路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_011_normalization.md`
改造类型：behavior-change（部分复用同事源码，改归一化模式）
真机风险等级：none
L2 Git 分支：`feat/model_deploy/l2-03-assembly`
验收证据目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/`
对应 L2 运行验收场景：S3
验收卡片路径：`DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_011_验收卡片.md`
验收模式：direct-local
辅助验收模式：无
本地验收是否必须：true
验收反馈目录：`DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs/`

> [!warning] 产物落点约束
> 本 L3 产出的所有文件必须落到 `ACT代码树分层与产物落点约束.md` 规定的唯一位置。

## 2. 调度元数据

```yaml
dispatch:
  task_id: deploy_011
  task_file: DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-03-assembly/deploy_011_normalization.md
  group: l2-03-assembly
  branch: feat/model_deploy/l2-03-assembly
  integration_branch: model_deploy
  acceptance_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly
  acceptance_scenarios: [S3]
  acceptance_card: DOCS/03_工程/阶段四：模型部署/03_tasks/cards/l2-03-assembly/deploy_011_验收卡片.md
  acceptance_mode: direct-local
  acceptance_secondary_modes: []
  local_acceptance_required: true
  acceptance_round_limit: 3
  acceptance_feedback_dir: DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-03-assembly/logs
  wave: 1
  parallel_group: l2-03-assembly-w1
  depends_on: []
  must_run_after: []
  can_run_parallel_with: [deploy_009, deploy_010]
  blocks: [deploy_012]
  conflict_scope:
    files:
      - src/model_deploy/act/repo/normalization.py
    modules:
      - act.repo.normalization
    config_keys: []
    runtime_modes: []
    hardware_paths: []
  robot_risk: none
  dispatch_status: ready
```

## 3. 本次唯一目标

```text
新建 src/model_deploy/act/repo/normalization.py，提供 ACT 的 state/action 归一化与反归一化。
部分复用同事 ActionStateNormalizer 类（通用归一化逻辑），但归一化模式从 min-max 改为 mean-std
（ACT 默认 NormalizationMode.MEAN_STD）。从 normalizers.json（mean/std 数组）重建 normalizer。
剥离同事的 build_normalizer_from_lerobot / build_state_action_normalizers（训练侧工厂，部署不用）。
```

## 4. 来源契约

| 字段 | 内容 |
|---|---|
| Delta | A5 |
| AS-IS | 同事 `normalization.py`（310行）：`ActionStateNormalizer`（min-max 归一化到 [-1,1]，支持 identity 维度透传）+ `build_normalizer_from_lerobot`/`build_state_action_normalizers`（从 LeRobotDataset 算 stats）+ `ensure_vector_stats`。 |
| TO-BE | 保留 `ActionStateNormalizer` 类框架，改归一化模式为 mean-std（`y=(x-mean)/std`，反归一化 `x=y*std+mean`）。新增 `load_normalizers_from_json(path)` 从 normalizers.json 重建。剥离训练侧工厂。 |

所属 L2：[[L2-03-ACT数据装配与模型加载]]，契约：[[ACT模型训练交付物契约]]（normalizers.json mean-std）。

## 5. 现有程序盘点

| 现有对象 | 路径 | 行数 | 已有能力 | 复用方式 |
|---|---|---|---|---|
| `ActionStateNormalizer` | `pi05_old/.../common/data/normalization.py` | ~100 | min-max normalize/unnormalize + identity 透传 | **部分复用**（类框架保留，归一化公式改 mean-std） |
| `build_normalizer_from_lerobot()` | 同文件 | ~60 | 从 LeRobotDataset.stats 构建 | **不搬**（训练侧，部署从 JSON 重建） |
| `build_state_action_normalizers()` | 同文件 | ~40 | 从 dataset 构建 state+action normalizer | **不搬** |
| `ensure_vector_stats()` | 同文件 | ~30 | 检查/修复 stats 格式 | **不搬**（pi05 专用，可能覆写 stats.json） |
| `_VectorStatsAccumulator` | 同文件 | ~40 | pooled variance 累加器 | **不搬**（训练侧） |

> [!note] 复用要点
> 同事 `ActionStateNormalizer` 的核心价值是「统一的 normalize/unnormalize 接口 + identity 维度透传」。这个框架保留，只把内部的 min-max 公式换成 mean-std。归一化参数不再从 LeRobotDataset 算，而是直接从部署 bundle 的 `normalizers.json`（mean/std 数组）读取。

## 6. 真实改造边界

### 本次允许做

- 新建 `src/model_deploy/act/repo/normalization.py`：
  - `ActionStateNormalizer` 类（mean-std 版）：`__init__(mean, std, identity_indices=())`；`normalize(x)` = `(x-mean)/std`；`unnormalize(y)` = `y*std+mean`；identity 维度透传。
  - `load_normalizers_from_json(path) -> tuple[ActionStateNormalizer, ActionStateNormalizer]`：读 normalizers.json，返回 (state_normalizer, action_normalizer)。
  - 校验 mean/std 数组长度 == 16（对照 ACTION_DIM/STATE_DIM）。
- 新建 `act/tests/repo/test_normalization.py`。

### 本次不做

- 不搬训练侧工厂（build_*_from_lerobot）。
- 不搬 ensure_vector_stats。
- 不改 policy_loader（deploy_009 import 本 L3 的 normalizer）。

### 明确禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/**`、`act/config/**`、`act/runtime/**`、`act/service/**`

## 7. 实施步骤

1. 先 Read 同事 `normalization.py` 全文，理解 `ActionStateNormalizer` 的 normalize/unnormalize/identity 实现。
2. 新建 `act/repo/normalization.py`：
   - `ActionStateNormalizer`（mean-std 版，保留 identity 透传）。
   - `load_normalizers_from_json(path)`：`json.load` → 取 `state.mean/state.std/action.mean/action.std` → 构造两个 normalizer。校验长度 16。
3. 新建 `act/tests/repo/test_normalization.py`：
   - 构造 mean/std 数组 → normalize → unnormalize round-trip 等于原始（非 identity 维度）。
   - identity 维度透传（normalize 返回原值）。
   - load_normalizers_from_json 从 mock json 重建，长度校验。
4. 运行 pytest。

## 8. 验证方式

```bash
cd /home/hit/ROS
pytest src/model_deploy/act/tests/repo/test_normalization.py -v
```

| 层级 | 通过标准 |
|---|---|
| unit | mean-std normalize/unnormalize round-trip；identity 透传；JSON 加载长度校验 |

L2 贡献：mean-std 归一化就绪，供 policy_loader（deploy_009）使用。

## 9. 允许修改

| 产物 | 落点路径 | 所属层 |
|---|---|---|
| normalization 源码 | `src/model_deploy/act/repo/normalization.py` | repo |
| 单测 | `src/model_deploy/act/tests/repo/test_normalization.py` | tests/repo |

## 10. 禁止修改

- `pi05/**`、`third_party/**`、`pi05_old/**`
- `act/types/**`、`act/config/**`、`act/runtime/**`、`act/service/**`

## 11. 必读上下文

### 必读任务文档
- `DOCS/03_工程/阶段四：模型部署/02_l2_change_packages/L2-03-ACT数据装配与模型加载.md`
- `DOCS/03_工程/阶段四：模型部署/01_contracts/ACT模型训练交付物契约.md`（normalizers.json mean-std 示例）

### 必读代码（AS-IS 参考）
- `DOCS/03_工程/阶段四：模型部署/pi05_old/pi05_test/pi05/common/src/pi05/common/data/normalization.py`（310行，ActionStateNormalizer 参考）

### 必读约束文档
- `DOCS/02_约束/编程执行/架构边界与机械约束原则.md`（第三节 shape 边界校验）
- `DOCS/02_约束/工作流/阶段四开发工作流/attachments/ACT代码树分层与产物落点约束.md`

## 12. 执行要求

- 身份校验：分支 `feat/model_deploy/l2-03-assembly`。
- 依赖：L2-01（ACTION_DIM=16/STATE_DIM=16 常量用于长度校验）。
- TDD：先写 round-trip 单测。
- 落点校验。

## 13. 成功标准

- [ ] `act/repo/normalization.py` 存在，含 `ActionStateNormalizer`（mean-std）+ `load_normalizers_from_json`。
- [ ] normalize = (x-mean)/std；unnormalize = y*std+mean。
- [ ] identity 维度透传。
- [ ] load_normalizers_from_json 校验数组长度 16。
- [ ] `test_normalization.py` PASSED。
- [ ] 未修改 pi05/types/config/runtime/service。

## 14. 回滚方式

删除 `src/model_deploy/act/repo/normalization.py`。

## 15. 完成后交接

（执行 sub-agent 完成后填写）
