# repo 层设计：L2-01

## 1. 目标源码路径

```text
src/model_deploy/act/repo/bundle_reader.py
src/model_deploy/act/repo/manifest_parser.py
src/model_deploy/act/repo/normalizer_loader.py
src/model_deploy/act/repo/experiment_config_loader.py
```

## 2. 层职责

`repo/` 负责进程外资源读取和反序列化。它只做路径、文件存在性、格式读取，不做业务维度校验；业务校验归 `config/`。

## 3. 文件设计

| 文件 | 职责 | 输入 | 输出 | 副作用 |
|---|---|---|---|---|
| `bundle_reader.py` | bundle 目录检查、checkpoint 路径解析 | bundle dir | checkpoint path / exception | 文件系统 stat |
| `manifest_parser.py` | 读取 manifest.json | bundle dir | manifest dict | 文件读取 |
| `normalizer_loader.py` | 读取 normalizers.json | bundle dir | normalizer objects | 文件读取 |
| `experiment_config_loader.py` | 读取 experiment_config.yaml | bundle dir | experiment config dict/object | 文件读取 |

## 4. 不负责内容

- 不做 ROS topic 读写。
- 不加载 ACT policy 到模型对象。
- 不做 state/action 维度业务校验。
- 不读写平滑处理或 RTC 对齐配置；这些第一版不进入 L2-01。

## 5. 验收覆盖

- 合法文件可读取。
- 缺文件抛明确异常。
- 坏 JSON/YAML 抛明确异常。
- 业务维度不一致交给 `config` 层 contract check。
