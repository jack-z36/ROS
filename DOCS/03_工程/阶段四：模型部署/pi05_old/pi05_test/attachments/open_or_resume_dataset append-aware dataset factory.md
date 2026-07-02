---
tags:
  - 附件
---

# open_or_resume_dataset (append-aware 数据集打开器)

> [!abstract]
> 工厂函数：根据目标目录是否存在决定是 `create` 还是 resume 现有 LeRobotDataset，保证多次 CLI 调用可以往同一个数据集里追加 episode。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 函数名 | `open_or_resume_dataset` |
| 入参 | `repo_id`, `root`, `features: dict`, `use_videos: bool = True` |
| 出参 | `LeRobotDataset` 实例（无论 create 还是 resume） |
| 所在文件 | `pi05_test/tools/mcap_to_lerobot_v3.py:347-432` |
| 现实含义 | 让 `mcap_to_lerobot_v3.py` 可以"先把 5 个 MCAP 转成 ep0..ep4，明天再把另外 3 个 MCAP 追加到 ep5..ep7" |

## 三种模式

| 模式 | 触发条件 | 行为 |
| --- | --- | --- |
| **create** | `root` 不存在 | `LeRobotDataset.create(repo_id, root, features, use_videos)` |
| **resume** | `root` 存在 + 已有 `meta/info.json` | `LeRobotDataset(repo_id, root)` 重新打开 |
| **不一致** | 已有但 `info.json` 的 features 与传入 features 不一致 | **抛 RuntimeError** 列出冲突的 key |

## 校验清单（resume 模式）

```text
1. 读 existing_info = load_info(root / "meta/info.json")
2. 检查传入的 features 键集合 == existing_info["features"] 键集合
   - 多出的 key：报"extra feature keys: ..."
   - 缺少的 key：报"missing feature keys: ..."
   - shape 不一致：报"feature X shape changed: Y → Z"
3. 全部一致 → LeRobotDataset(repo_id, root) 走 resume
4. 否则 → raise
```

## 为什么用 in-place 而非 LeRobotDataset.push_to_hub

- **本地优先**：本仓库目的是离线构建 LeRobot v3 本地 dataset，不是上传 HuggingFace
- **可重复**：删除 `root` 即可重新 build
- **支持 mixed FPS**：每个 episode 的 fps 都来自其 MCAP 的 top 相机，resume 时会自动取 max

## 在数据流中的位置

- **上游调用**：`convert_mcap_to_lerobot` (L2077) / `convert_mcap_to_lerobot_with_annotations` (L2280) / `convert_mcap_dir_to_lerobot` (L2356) 都会先调一次
- **下游消费**：返回的 `ds` 实例被传入 `_convert_one_mcap_into_dataset`，每个 episode 末尾 `ds.save_episode()`

## 关键约束

- **不校验视频文件是否完整**：resume 模式只校验 `meta/info.json`，不读 parquet/video。损坏的视频会在训练 dataloader 时报错
- **action/state 的 dtype 锁死 float32**：见 `build_features_pi05:282`，后续不能改
- **features 顺序无关**：是 dict 集合比较，不是 list 顺序比较
- 与 [[TactilePreprocessStats per-episode tactile stats]] 配合，tactile meta 单独校验
