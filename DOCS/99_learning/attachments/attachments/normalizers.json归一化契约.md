---
tags:
  - 附件
---

# normalizers.json归一化契约

> [!abstract]
> 一句话说明：这是 bundle 内保存 state/action 归一化参数的最终 JSON 文件，部署端用它重建两个 `ActionStateNormalizer`。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `NORMALIZERS_NAME`, `_normalizer_payload(...)`, `normalizer_path` |
| 参考系 | JSON 文件结构空间 |
| 相对原点 | bundle 根目录 |
| 物理锚点 | 无对应物理点，这是纯数学/尺度转换契约文件 |
| 阶段属性 | 最终 artifact |
| 是否最终输出 | 是 |
| 数据类型 | JSON file / `dict[str, Any]` |
| 数据结构 | 顶层包含 `state` 和 `action`，各自包含 `min`, `max`, `identity_indices` |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:19,50,65-83,155-170` |
| 现实含义 | 部署端恢复训练时 state/action 尺度的依据 |

## 关键澄清

### 1. 它在哪个参考系下？
在 bundle 文件结构空间下，不是空间坐标系。

### 2. 它相对哪个原点？
文件路径相对 [[deploy bundle输出目录]]。

### 3. 它对应哪个物理点 / 物理对象？
无对应物理点，这是纯数学对象；它保存尺度转换参数。

### 4. 它是不是最终输出？
是。

### 5. 它不是什么？
它不是数据集统计的完整副本；只保存部署所需的 min/max/identity 信息。

## 对应源码

```python
_write_json(output_dir / NORMALIZERS_NAME, _normalizer_payload(state_normalizer, action_normalizer))

def _normalizer_payload(state_normalizer, action_normalizer):
    return {
        "state": _single_normalizer_payload(state_normalizer),
        "action": _single_normalizer_payload(action_normalizer),
    }
```

## 一句话说清楚

> `normalizers.json` 是把训练数据尺度规则带到部署端的 JSON 契约。

## 在数据流中的位置

- 上游：[[state向量归一化器]]、[[action向量归一化器]]
- 下游：`load_bundle_normalizers()`、部署侧 `Pi05PolicyRuntime`

