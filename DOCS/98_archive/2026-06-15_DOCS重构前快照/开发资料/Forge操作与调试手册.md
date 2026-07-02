# Forge 操作与调试手册

## 1. 文档目的

本文面向 Linux 端 Codex。假设 Codex 对 forge 没有任何背景知识，但 Linux 环境中已经部署好 forge。

当前核心目标：

```text
使用一个已经对齐好的 MCAP 文件
  -> 测试 forge 是否能输出 LeRobotDataset v3
  -> 再使用 forge 评估输出数据集质量
  -> 判断位姿轨迹是否抖动、乱跳、绕路或时间戳异常
```

本手册只指导调试和使用 forge，不要求修改阶段二代码。

## 2. 当前路线

场景四 P0 暂时把 forge 当作数据清洗流程中的外部子程序：

```text
aligned MCAP
  -> forge inspect / config
  -> forge convert
  -> LeRobotDataset v3
  -> forge quality
```

第一版允许用户手动调用 forge。后续再把这些步骤融合绑定进 `data_clean`。

## 3. 术语

- `aligned MCAP`：场景三已经按统一 step 时间轴对齐后的 MCAP。
- `forge input MCAP`：准备交给 forge 读取的 MCAP。首轮可以直接用 aligned MCAP；如果自动识别失败，再整理为更规范的 forge 输入 MCAP。
- `LeRobotDataset v3`：forge 转换后的目标数据集目录。
- `quality report`：forge 对 LeRobotDataset v3 的质量评估结果。

## 4. 推荐工作目录

Linux 端建议新建一个独立调试目录，不要把测试输出散落到仓库根目录：

```bash
mkdir -p asset/阶段二：数据清洗/dev/forge_debug
cd asset/阶段二：数据清洗/dev/forge_debug
```

推荐目录结构：

```text
forge_debug/
├── input/
│   └── aligned_sample.mcap
├── config/
│   └── forge_topic_config.yaml
├── output/
│   └── lerobot_v3/
├── reports/
│   ├── inspect.json
│   ├── quality_report.json
│   └── debug_notes.md
└── logs/
    ├── forge_inspect.log
    ├── forge_convert.log
    └── forge_quality.log
```

如果用户已经给出 MCAP 绝对路径，先不要移动原始文件，可以复制或软链接到 `input/aligned_sample.mcap`。

## 5. 环境自检

先确认 forge 命令可用：

```bash
forge version
forge --help
```

确认 Python 能导入 forge：

```bash
python3 - <<'PY'
import forge
print("forge import ok")
print(getattr(forge, "__version__", "unknown"))
PY
```

确认常用依赖可用：

```bash
python3 - <<'PY'
mods = ["mcap", "mcap_ros2", "pyarrow", "yaml", "numpy"]
for name in mods:
    try:
        __import__(name)
        print(f"ok: {name}")
    except Exception as exc:
        print(f"missing_or_failed: {name}: {exc}")
PY
```

如果 `mcap` 或 `mcap_ros2` 不可用，forge 通常不能读取 ROS2 MCAP。

## 6. 输入 MCAP 最低要求

forge 要从 MCAP 转 LeRobot v3，至少需要从 MCAP 里读出：

```text
observation.state
action
observation.images.<camera_name>
timestamp
```

其中：

- `observation.state`：机器人当前状态。第一版建议是位姿位置 `[x, y, z]`，或固定长度状态向量。
- `action`：每一步动作。可以是下一步目标位姿、目标关节角或控制量，但必须是固定长度数值向量。
- `observation.images.<camera_name>`：每一步对应图像。
- `timestamp`：由 MCAP message timestamp 提供。

最稳的 MCAP topic 形态：

```text
/forge/observation/state       Float32MultiArray.data 或 JointState.position
/forge/action                  Float32MultiArray.data 或 JointState.position
/forge/observation/images/front Image 或 CompressedImage
```

topic 名不是硬要求，但语义清楚会降低调试成本。

## 7. 第一步：inspect 输入 MCAP

先看 forge 是否能识别 MCAP：

```bash
forge inspect input/aligned_sample.mcap 2>&1 | tee logs/forge_inspect.log
```

如果支持 JSON 输出：

```bash
forge inspect input/aligned_sample.mcap --output json > reports/inspect.json
```

重点观察：

- format 是否是 `mcap`。
- 是否能看到 cameras。
- 是否能推断 observation schema。
- 是否有 action schema。
- 是否提示 missing required。

如果 `forge inspect` 直接失败，先不要 convert。优先看：

- MCAP 文件路径是否正确。
- MCAP 是否损坏。
- 是否缺少 mcap 相关依赖。
- MCAP schema 是否是 forge 支持的 ROS2 / Foxglove 类型。

## 8. 第二步：生成或准备 topic config

forge 的 MCAP reader 需要知道哪些 topic 对应 `observation.state`、`action`、`observation.images.*`。

可以先让 forge 生成一个 starter config：

```bash
forge inspect input/aligned_sample.mcap --generate-config config/forge_topic_config.yaml
```

然后人工检查并编辑 `config/forge_topic_config.yaml`。

一个最小配置示例：

```yaml
source: ../input/aligned_sample.mcap

episodes:
  strategy: single
  min_length_frames: 1

fields:
  observation.state:
    topic: /forge/observation/state
    field: data
    dtype: float32

  action:
    topic: /forge/action
    field: data
    dtype: float32

  observation.images.front:
    topic: /forge/observation/images/front
    encoding: rgb8

sync:
  primary: observation.state
  method: nearest
  max_skew_ms: 5

task:
  description: "fastumi aligned sample"
```

如果 state/action 使用 `sensor_msgs/msg/JointState`，`field` 通常写：

```yaml
field: position
```

如果 state/action 使用 `std_msgs/msg/Float32MultiArray`，`field` 通常写：

```yaml
field: data
```

## 9. 第三步：尝试 CLI 转换

先尝试最普通的转换：

```bash
forge convert input/aligned_sample.mcap output/lerobot_v3 --format lerobot-v3 2>&1 | tee logs/forge_convert.log
```

转换成功后，检查输出目录：

```bash
find output/lerobot_v3 -maxdepth 3 -type f | sort | head -100
```

期望看到类似：

```text
output/lerobot_v3/meta/info.json
output/lerobot_v3/meta/tasks.parquet
output/lerobot_v3/meta/stats.json
output/lerobot_v3/data/chunk-000/file-000.parquet
output/lerobot_v3/videos/...
```

如果 CLI 支持把 topic config 传给 convert，可以尝试：

```bash
forge convert input/aligned_sample.mcap output/lerobot_v3 --format lerobot-v3 --config config/forge_topic_config.yaml 2>&1 | tee logs/forge_convert.log
```

注意：不同 forge 版本对 `--config` 的含义可能不同。有些版本的 `--config` 是通用 conversion config，不一定等同于 MCAP topic config。若 CLI 不能按 topic config 转换，使用下一节 Python fallback。

## 10. Python fallback：显式传入 MCAP TopicConfig

如果 CLI 不能正确使用 `forge_topic_config.yaml`，用 Python 直接调用 forge MCAP reader 和 LeRobot v3 writer。

创建临时脚本：

```bash
cat > run_forge_mcap_to_lerobot.py <<'PY'
from pathlib import Path

from forge.core.models import DatasetInfo
from forge.formats.mcap import MCAPReader, load_config
from forge.formats.lerobot_v3 import LeRobotV3Writer, LeRobotV3WriterConfig

input_mcap = Path("input/aligned_sample.mcap")
topic_config = load_config("config/forge_topic_config.yaml")
output_dir = Path("output/lerobot_v3")

reader = MCAPReader()
episodes = list(reader.read_episodes(input_mcap, config=topic_config))

if not episodes:
    raise SystemExit("No episodes read from MCAP")

total_frames = sum(ep.num_frames or len(ep.load_frames()) for ep in episodes)
fps = episodes[0].fps or 30.0

writer = LeRobotV3Writer(
    LeRobotV3WriterConfig(
        fps=fps,
        robot_type="fastumi",
    )
)

dataset_info = DatasetInfo(
    path=input_mcap,
    format="mcap",
    num_episodes=len(episodes),
    total_frames=total_frames,
    inferred_fps=fps,
    inferred_robot_type="fastumi",
)

writer.write_dataset(iter(episodes), output_dir, dataset_info=dataset_info)

print(f"converted episodes: {len(episodes)}")
print(f"converted frames: {total_frames}")
print(f"output: {output_dir}")
PY
```

运行：

```bash
python3 run_forge_mcap_to_lerobot.py 2>&1 | tee logs/forge_convert.log
```

如果这个 fallback 成功，说明 forge 核心库可用，问题只在 CLI config 传参路径。

## 11. 第四步：inspect 输出 LeRobotDataset v3

转换后必须检查输出数据集是否能被 forge 读取：

```bash
forge inspect output/lerobot_v3 2>&1 | tee logs/forge_lerobot_inspect.log
```

如果支持 JSON：

```bash
forge inspect output/lerobot_v3 --output json > reports/lerobot_inspect.json
```

重点看：

- format 是否为 `lerobot-v3`。
- episodes 是否大于 0。
- total frames 是否大于 0。
- observation schema 是否包含 `observation.state`。
- action schema 是否存在。
- cameras 是否存在。
- timestamps 是否存在。

## 12. 第五步：使用 forge 评估数据集质量

运行质量评估：

```bash
forge quality output/lerobot_v3 --export reports/quality_report.json 2>&1 | tee logs/forge_quality.log
```

如果知道 fps：

```bash
forge quality output/lerobot_v3 --fps 30 --export reports/quality_report.json 2>&1 | tee logs/forge_quality.log
```

如果 action 有已知范围，比如归一化到 `[-1, 1]`：

```bash
forge quality output/lerobot_v3 --fps 30 --action-bounds -1,1 --export reports/quality_report.json 2>&1 | tee logs/forge_quality.log
```

质量评估重点字段：

- `overall_score`：总体质量，0 到 10。
- `ldlj` / smoothness：轨迹平滑度，越差通常代表越抖或 jerk 越大。
- `joint_path_length`：路径长度，异常大可能代表绕路、乱跳或坐标抖动。
- `timestamps`：时间戳是否规律。
- `static`：是否长时间不动。
- `flags`：forge 标记的问题。

## 13. 位姿轨迹质量如何判断

如果目标是看“位姿轨迹是不是很乱”，建议首轮让：

```text
observation.state = [tcp_x, tcp_y, tcp_z]
```

这样 forge 的 smoothness 和 path length 最容易解释。

不建议第一轮直接把原始四元数放进 state：

```text
[x, y, z, qx, qy, qz, qw]
```

原因是 `q` 和 `-q` 表示同一个姿态，但数值上可能突然跳变，forge 会把这种跳变当成轨迹抖动。

如果确实要评估姿态，建议使用连续展开后的欧拉角：

```text
[x, y, z, roll, pitch, yaw]
```

并在报告里注明角度是否已经 unwrap。

## 14. 常见问题与排查

### 14.1 forge inspect 不能识别 MCAP

检查：

```bash
ls -lh input/aligned_sample.mcap
file input/aligned_sample.mcap
python3 - <<'PY'
from mcap.reader import make_reader
with open("input/aligned_sample.mcap", "rb") as f:
    reader = make_reader(f)
    print(reader.get_summary())
PY
```

如果这里都失败，问题在 MCAP 文件本身或 mcap 依赖，不在 LeRobot 转换。

### 14.2 inspect 能识别，但 convert 没有 action/state

通常是 topic 映射失败。

处理：

- 打开 `logs/forge_inspect.log` 看 topic 列表。
- 确认 state/action topic 是否存在。
- 确认 `field` 是 `data` 还是 `position`。
- 使用 Python fallback 显式传入 `forge_topic_config.yaml`。

### 14.3 图像转换失败

常见原因：

- 图像不是 `sensor_msgs/Image` / `sensor_msgs/CompressedImage` / Foxglove 支持类型。
- compressed image 编码不被当前环境解码。
- 缺少视频依赖，例如 PyAV。

先用只含 state/action 的最小 MCAP 测通，再加图像。

### 14.4 quality 结果为空或没有 smoothness

说明 forge 没有读到 `observation.state` 或 state 不是数值矩阵。

检查 LeRobot 输出：

```bash
forge inspect output/lerobot_v3 --output json | jq '.observation_schema'
```

如果没有 `observation.state`，回到 topic config 和转换步骤排查。

### 14.5 smoothness 很差

可能原因：

- 位姿本身抖动。
- 时间戳不均匀。
- 坐标系混乱，左右手或 camera/base frame 混用。
- 四元数符号翻转导致数值跳变。
- 单位不一致，比如部分样本是 mm，部分样本是 m。

优先检查：

- state 是否只用 `[x, y, z]`。
- 单位是否统一为 m。
- 时间戳间隔是否稳定。
- 是否存在异常大跳变。

## 15. Codex 协作要求

Linux 端 Codex 执行本手册时，应当像用户的调试助手，而不是只机械运行命令。

每一步都要回答：

1. 当前命令验证什么？
2. 成功时应该看到什么？
3. 失败时最可能是哪一层问题？
4. 下一步该缩小哪个范围？

遇到失败时，不要直接重装环境或改代码。优先按层定位：

```text
文件存在性
  -> forge 命令可用性
  -> mcap 依赖
  -> MCAP 可读性
  -> topic/schema 可识别
  -> topic config 映射
  -> LeRobot v3 写出
  -> quality 评估
```

## 16. 最小成功定义

本次 forge 试验最小成功标准：

- `forge inspect input/aligned_sample.mcap` 能读到 MCAP。
- 能转换出 `output/lerobot_v3/`。
- `forge inspect output/lerobot_v3` 能识别为 LeRobotDataset v3。
- `forge quality output/lerobot_v3 --export reports/quality_report.json` 能生成质量报告。
- 报告中能看到 smoothness / path length / timestamp regularity 等信息。

如果以上全部满足，说明 forge 可作为场景四 P0 子程序继续推进。
