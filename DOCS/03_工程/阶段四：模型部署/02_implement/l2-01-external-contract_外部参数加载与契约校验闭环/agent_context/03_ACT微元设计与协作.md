# ACT 微元设计与协作：L2-01

## 1. 设计原则

L2-01 只负责静态契约进入 RAM。它为后续 L2 提供清晰、不可变、可校验的配置和规格对象，不参与稳态运行时调度。

第一版已去除独立平滑处理：本 L2 不定义 action smoothing、smoothstep blend、跨 chunk 融合、RTC 类平滑或复杂时间对齐配置。L2-06 只消费本 L2 暴露的 `chunk_size`、`control_hz`、fallback 策略和最小 cursor 所需配置。

## 2. ACT 微元设计

| ACT 微元 | 3.5 类型 | target layer | target file | function/class | 输入 | 输出 | 副作用 | Pi0.5 参考 |
|---|---|---|---|---|---|---|---|---|
| 16D StateSpec | 数据 | types | `src/model_deploy/act/types/state_spec.py` | class + codec 函数 | 结构化 observation state | flat 16D state / 校验异常 | 无 | `common/data/state_codec.py` |
| 16D ActionSpec | 数据 | types | `src/model_deploy/act/types/action_spec.py` | class + codec 函数 | flat 16D action | 分段 action / 校验异常 | 无 | `common/robot/action_spec.py` |
| ContractResult | 数据 | types | `src/model_deploy/act/types/contract_result.py` | frozen dataclass | 校验事实 | pass/fail 结果对象 | 无 | ACT 增量 |
| DeployConfig | 数据 + 计算函数 | config | `src/model_deploy/act/config/schema.py` | frozen dataclass | 子配置 | 聚合根配置 | 无 | `deploy/config/schema.py` |
| 类型化校验器 | 计算函数 | config | `src/model_deploy/act/config/schema.py` | function | raw value | typed value / exception | 无 | Pi0.5 校验器群 |
| bundle reader | 数据读写函数 | repo | `src/model_deploy/act/repo/bundle_reader.py` | function | bundle dir | 文件存在性 / checkpoint path | 文件系统读取 | `common/runtime/bundle.py` |
| manifest parser | 数据读写函数 | repo | `src/model_deploy/act/repo/manifest_parser.py` | function | manifest path | dict | 文件读取 | `common/runtime/bundle.py` |
| normalizer loader | 数据读写函数 | repo | `src/model_deploy/act/repo/normalizer_loader.py` | function | normalizers path | normalizer objects | 文件读取 | `common/data/normalization.py` |
| experiment config loader | 数据读写函数 | repo | `src/model_deploy/act/repo/experiment_config_loader.py` | function | experiment yaml | config object/dict | 文件读取 | `common/config/schema.py` |

## 3. 内部协作关系

```text
Creation order:
1. repo 层读取 deploy.yaml / manifest / normalizers / experiment_config / checkpoint path。
2. types 层提供 StateSpec / ActionSpec / ContractResult。
3. config 层将 raw mapping 转为 DeployConfig。
4. config 层交叉校验 manifest、experiment_config、normalizers 与 16D 契约。

State owner:
DeployConfig、StateSpec、ActionSpec 是启动期创建、全生命周期只读的 RAM 对象。

Pure RAM calculations:
类型化校验器、维度一致性校验、topic namespace 校验、fallback 策略枚举校验。

External boundary reads/writes:
repo 层读文件系统；本 L2 不写外部文件、不订阅 topic、不发布 topic。

Runtime orchestration point:
无。本 L2 不进入稳态 tick；L2-06 读取 RuntimeConfig 后自行维护 active chunk 与 cursor。

Failure propagation:
配置或契约非法时，启动阶段直接失败，不进入半初始化状态。
```

## 4. 去除平滑处理后的协作影响

- `RuntimeConfig` 不提供 `blend_steps`、`smoothstep_window`、`cross_chunk_fusion`、`rtc_alignment` 等字段。
- `ActionSpec` 只定义单步 action 的 16D 契约，不定义 chunk 平滑规则。
- `DeployConfig` 只提供第一版 cursor 消费需要的 `chunk_size`、`control_hz`、`fallback_policy`、`max_action_age_sec` 等最小调度配置。
- L2-06 若后续要引入平滑优化，必须新增设计变更并同步更新 L1/L2 文档和 Gate；不得从 L2-01 暗含未声明配置。
