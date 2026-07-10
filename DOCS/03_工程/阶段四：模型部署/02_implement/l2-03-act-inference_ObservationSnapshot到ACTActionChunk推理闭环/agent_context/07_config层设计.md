# config 层设计：L2-03

## 1. 本 L2 不在该层新增源码产物

L2-03 消费 L2-01 已构造并校验的 `DeployConfig`，不创建第二套 inference schema，也不把业务计算放进 config。

## 2. L2-03 实际消费的配置语义

| 配置语义 | 使用阶段 | 用途 | 禁止用途 |
|---|---|---|---|
| `runtime.state_dim` | service 创建/阶段一 | 与 state normalizer、snapshot state 契约共同确认 16D | 运行中改写 state 维度 |
| `runtime.action_dim` | service 创建/阶段三 | 确认输出最后一维为 16 | 把错误输出投影、裁剪为 16D |
| `runtime.chunk_size` | service 创建/阶段三 | 确认 raw/final 的行数严格相等 | 对过长 chunk 截断或对过短 chunk padding |
| `runtime.device` | 阶段一 | batch 与已加载 policy device 对齐 | 自动回退到另一设备或重新移动 policy |
| policy input features | service 创建/阶段一 | 获取必需图像 full key、shape 与顺序 | 按 snapshot dict 顺序推断相机 |

最后一行来自已加载 policy 的 RAM 元数据，不是 L2-03 新增 config 文件。

## 3. L2-03 明确不消费的配置语义

以下字段由其他 L2 所有，L2-03 不读取它们来决定分支或行为：

| 字段类别 | 所有者 | 原因 |
|---|---|---|
| bundle 路径、checkpoint、adapter、manifest | L2-01 | L2-03 不读资源、不加载 policy |
| mode、real/test policy 选择 | L2-01/L2-06 | L2-03 只接受已注入 policy |
| inference_hz、control_hz、execute_horizon、prefetch | L2-06 | 调度频率、chunk 消费和预取不属于同步服务 |
| queue 容量、fallback、warmup、metrics 周期 | L2-06 | 属于 runtime 状态机和观测 |
| safety TCP/gripper 限制、quaternion 开关 | L2-04 | L2-03 不做 safety 或 clamp |
| command/observation topics | L2-06/L2-05 | L2-03 没有 ROS I/O |
| image resize/transport 参数 | L2-02 | snapshot 到达前已完成图像像素级预处理 |
| compile/device 初始化选项 | L2-01 | policy 在注入前已经完成启动配置 |

## 4. 不允许新增的配置

- 不新增 `inference` 子 schema。
- 不新增 fake-policy 开关。
- 不新增 `clamp_normalized_action`、`output_crop_size`、`pad_action_chunk`。
- 不新增 `blend_steps`、`smoothing`、`temporal_ensemble`、RTC 或 cursor 配置。
- 不把训练侧 image mean/std 等未声明资源偷偷加入 L2-03；若模型需要额外图像统计量，应先在 L1/L2-01/L2-02 契约中显式定义。

## 5. 验收

- L2-03 不新增 `src/model_deploy/act/config/*.py`。
- 测试通过注入合法 `DeployConfig` 和 policy fixture 建 service。
- config/policy chunk/action/device 不一致时失败，不出现隐式修补。
- 静态扫描不应发现 fake、clamp、smoothing、queue 或 bundle loader 的新配置分支。

## 6. 边界声明

`DeployConfig` 是稳定输入，不是本 L2 产出；L2-03 不写回或修改 config。
