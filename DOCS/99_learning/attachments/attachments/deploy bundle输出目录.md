---
tags:
  - 附件
---

# deploy bundle输出目录

> [!abstract]
> 一句话说明：这是部署 bundle 的根目录，所有最终 artifact 都写在它下面，部署端也以它作为唯一入口。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 变量名 | `output_dir`, `bundle_dir` |
| 参考系 | 文件系统路径空间 |
| 相对原点 | 调用方传入路径；代码会解析为绝对路径 |
| 物理锚点 | 无对应物理点，这是文件系统目录 |
| 阶段属性 | 最终输出容器 |
| 是否最终输出 | 是 |
| 数据类型 | `Path` |
| 数据结构 | 一个目录，包含 manifest、normalizers、配置镜像、adapter 和可选触觉文件 |
| 所在文件 | `pi05_test/pi05/common/src/pi05/common/runtime/bundle.py:29,34,38-55,58-91` |
| 现实含义 | 可以拷贝到部署机器上的最小运行时包 |

## 关键澄清

### 1. 它在哪个参考系下？
文件系统路径参考系。

### 2. 它相对哪个原点？
函数入口传入值可能相对当前工作目录；内部通过 `resolve()` 变为绝对路径。

### 3. 它对应哪个物理点 / 物理对象？
无对应物理点，这是文件系统目录。

### 4. 它是不是最终输出？
是。它是 `export_deploy_bundle()` 的核心输出容器，也是返回值所指向的目录。

### 5. 它不是什么？
它不是单个模型文件；它是多个部署 artifact 的目录协议。

## 对应源码

```python
output_dir = output_dir.expanduser().resolve()
_prepare_output_dir(output_dir, overwrite=overwrite)
...
return output_dir
```

## 一句话说清楚

> `output_dir/bundle_dir` 是部署包根目录，训练侧往里写，部署侧从这里读。

## 在数据流中的位置

- 上游：训练配置 `logging.run_export_dir` 或 CLI `--output-dir`
- 下游：[[adapter运行时权重目录]]、[[manifest.json部署清单契约]]、[[normalizers.json归一化契约]]、[[函数返回值 bundle根目录]]

