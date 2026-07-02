---
tags:
  - 附件
---

# 函数返回值 bundle根目录

> [!abstract]
> 一句话说明：这是 `export_deploy_bundle()` 最后返回的 `Path`，只指向已经写好的 bundle 根目录，不新增任何计算。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `return output_dir` |
| 参考系 | 文件系统路径空间 |
| 相对原点 | 已解析后的绝对 bundle 根目录 |
| 物理锚点 | 无对应物理点，这是返回值拼装 |
| 阶段属性 | 返回值拼装 |
| 是否最终输出 | 是 |
| 数据类型 | `Path` |
| 数据结构 | 单个路径对象，指向 bundle 根目录 |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:55` |
| 现实含义 | 调用方拿到导出结果位置，用于打印、拷贝或传给部署配置 |

## 关键澄清

### 1. 它在哪个参考系下？
文件系统路径空间。

### 2. 它相对哪个原点？
函数内已经 `resolve()`，所以返回值通常是绝对路径。

### 3. 它对应哪个物理点 / 物理对象？
无对应物理点，这是返回值拼装；它只是指向目录。

### 4. 它是不是最终输出？
是，但它不是新增文件，只是已生成 bundle 的路径引用。

### 5. 它不是什么？
它不是一个新的处理节点，不会在返回时重新生成 manifest 或 normalizers。

## 对应源码

```python
_write_json(output_dir / MANIFEST_NAME, _manifest_payload(...))
return output_dir
```

## 一句话说清楚

> `return output_dir` 只是把已完成的 bundle 根路径交还给调用方。

## 在数据流中的位置

- 上游：[[deploy bundle输出目录]]
- 下游：训练器日志打印或 CLI 输出

