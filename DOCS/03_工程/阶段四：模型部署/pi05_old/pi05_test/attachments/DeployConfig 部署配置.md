---
tags:
  - 附件
---

# DeployConfig (部署配置)

> [!abstract]
> `pi05_vla_deploy_node.py` 启动时加载的强类型 YAML 配置（来自 `pi05.deploy.config.schema.DeployConfig`），由 7 个子 dataclass 组成，是节点与 CLI 之间的唯一契约。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 类名 | `DeployConfig` (frozen dataclass) |
| 加载方式 | `load_deploy_config(path)` from `pi05.deploy.config.__init__` |
| YAML 路径 | 通过 `--config` CLI 参数传入（默认 `deploy/config/deploy.yaml`） |
| 位置 | `pi05_test/pi05/deploy/src/pi05/deploy/config/schema.py:240-264` |
| 现实含义 | 描述"这次部署用什么模型、走什么 ROS topic、按多少 Hz 控制、要保留哪些安全约束" |

## 子配置清单

| 字段 | 类型 | 默认 | 含义 |
| --- | --- | --- | --- |
| `bundle` | `BundleConfig` | 必填 | 训练导出的模型包目录（`config.bundle.resolved_bundle_dir`） |
| `runtime` | `RuntimeConfig` | 见 [[RuntimeConfig 部署运行时配置]] | 模式、设备、Hz、chunk 等 |
| `image` | `ImageConfig` | 224/resize_pad/raw | 图像预处理 + 传输 |
| `topics` | `TopicsConfig` | 必填 | 4 组 ROS topic 名 |
| `safety` | `SafetyConfig` | 见 [[SafetyConfig 安全配置]] | 关节 delta、stale 超时、夹爪范围 |
| `bridge` | `BridgeConfig` | 关闭 | 兼容旧执行栈的可选桥接 |
| `mux` | `MuxConfig` | 关闭 | teleop / VLA 多路复用器 |

## YAML 顶层结构示例

```yaml
bundle:
  bundle_dir: /opt/pi05/bundles/pour_demo
runtime:
  mode: dry-run           # dry-run | shadow-run | safe-run
  inference_hz: 10.0
  control_hz: 30.0
  chunk_size: 30
  execute_horizon: 10
image:
  image_size: 224
  resize_mode: resize_pad
  transport: raw           # raw | compressed | both
topics:
  namespace: /pi05_vla
  observation: { ... }     # 见 Pi05ObservationTopics
  command: { ... }         # 见 Pi05CommandTopics
safety:
  max_joint_delta_rad: 0.08
  stale_observation_timeout_s: 0.5
```

## 校验时机

`RuntimeConfig.__post_init__` (schema.py:65-91) 在 `from_mapping` 末尾做硬校验：
- `control_hz > 0`、`inference_hz > 0`
- `execute_horizon <= chunk_size`
- `prefetch_steps <= execute_horizon`
- `fallback_policy ∈ {hold_last_action, continue_old_chunk, safe_stop}`

任何不满足 → `DeployConfigError` 抛出，节点不会启动。

## 关键约束

- **部署配置与训练配置分离**：见 `schema.py:1-5` 文档字符串 "Deployment config is intentionally separate from training config"
- **`raw` 字段保留原 dict**：方便 `to_tracker_config()` 把整个 YAML 镜像到日志系统
- **topic 命名空间通过 `with_namespace`**：默认 `/pi05_vla`，可在 YAML `topics.namespace` 覆盖
- 与 [[RuntimeConfig 部署运行时配置]]、[[Pi05VlaDeployNode ROS2 部署节点]] 是上下游
