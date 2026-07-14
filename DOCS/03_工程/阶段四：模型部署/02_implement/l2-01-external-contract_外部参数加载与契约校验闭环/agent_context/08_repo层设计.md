# repo 层设计：L2-01

## 1. 目标源码路径

```text
src/model_deploy/act/repo/bundle_reader.py
src/model_deploy/act/repo/manifest_parser.py
src/model_deploy/act/repo/normalizer_loader.py
src/model_deploy/act/repo/experiment_config_loader.py
src/model_deploy/act/repo/act_runtime_resources.py   # deploy_056 启动资源合同唯一 owner
```

## 2. 层职责

`repo/` 负责进程外资源读取和反序列化。它只做路径、文件存在性、格式读取，不做业务维度校验；业务校验归 `config/`。

`act_runtime_resources.py` 是 L2-01 启动期资源合同的**唯一公开 owner**（deploy_056 / P0-01..04）：
它从生产 bundle 的 metadata（manifest + experiment_config）一次性派生冻结的
`PolicyInputSpec`，聚合已加载 policy、state/action normalizer 与交叉校验结果，得到
冻结的 `ActRuntimeResources`。下游 L2-02/03/06 只消费该合同，不得各自重建 spec。

## 3. 文件设计

| 文件 | 职责 | 输入 | 输出 | 副作用 |
|---|---|---|---|---|
| `bundle_reader.py` | bundle 目录检查、checkpoint 路径解析 | bundle dir | checkpoint path / exception | 文件系统 stat |
| `manifest_parser.py` | 读取 manifest.json | bundle dir | manifest dict | 文件读取 |
| `normalizer_loader.py` | 读取 normalizers.json | bundle dir | normalizer objects | 文件读取 |
| `experiment_config_loader.py` | 读取 experiment_config.yaml | bundle dir | experiment config dict/object | 文件读取 |
| `act_runtime_resources.py` | 启动资源聚合 + spec 唯一派生 | `DeployConfig` + 注入 `load_policy` | `ActRuntimeResources`（`PolicyInputSpec` / normalizers / policy / cross_check） | 文件系统 stat；不加载权重 |

### `act_runtime_resources.py` 设计要点（deploy_056）

- `PolicyInputSpec`：冻结，字段固定为 `state_key / state_dim / image_prefix /
  camera_keys / image_shapes / image_layout / image_dtype / image_value_range /
  action_dim / chunk_size`；构造不变量是 16D state/action、非空且唯一有序
  camera keys、精确 `(3, H>0, W>0)` CHW 三通道正尺寸、`float32`、`[0.0, 1.0]`、
  正 chunk。
- `ActRuntimeResources`：冻结，只聚合已加载 policy、state/action normalizer、
  同一个 `PolicyInputSpec` 和交叉校验结果。
- `load_act_runtime_resources(config, *, load_policy)`：唯一生产聚合入口。
  - spec 维度（state/action/chunk）**只**从生产 metadata 派生；metadata 缺失或
    与 config 冲突即启动 FAIL，config default 不得补洞。
  - `bundle_dir` 为 `None`/空时稳定失败，绝不猜路径。
  - policy 权重不在本层加载（属 L2-03）：生产通过注入的 `load_policy` 回调或
    `register_policy_loader` 提供；测试注入替身（fake-policy-test 模式）。

## 4. 不负责内容

- 不做 ROS topic 读写。
- 不加载 ACT policy 到模型对象（权重加载属 L2-03；本层只聚合已加载 policy）。
- 不做 state/action 维度业务校验（交给 `config` 层 contract check）。
- 不读写平滑处理或 RTC 对齐配置；这些第一版不进入 L2-01。
- 不另设第二份 spec、私有 spec、第二个 resource loader 或持久化 command enabled。

## 5. 验收覆盖

- 合法文件可读取。
- 缺文件抛明确异常。
- 坏 JSON/YAML 抛明确异常。
- 业务维度不一致交给 `config` 层 contract check。
- `PolicyInputSpec` / `ActRuntimeResources` 冻结且公开；`load_act_runtime_resources`
  对缺 metadata、维度/chunk 冲突、camera/image 冲突、normalizer 冲突、空 bundle
  均 fail-fast。

