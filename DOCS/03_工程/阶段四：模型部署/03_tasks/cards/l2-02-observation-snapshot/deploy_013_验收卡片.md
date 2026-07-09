# 验收卡片：deploy_013 图像预处理 ImagePreprocess

> [!info] 归属
> - 所属 L2：`l2-02-observation-snapshot`
> - L3 编号：`deploy_013`
> - 验收模式：`direct-local`
> - 验收轮次上限：3
> - 验收 Agent 只读，不得改源码、测试、dispatch 或 Git 状态。

| L3 编号 | `deploy_013` |
| 验收模式 | `direct-local` |
## 1. 检查对象

| 字段 | 值 |
|---|---|
| L3 任务文件 | `DOCS/03_工程/阶段四：模型部署/03_tasks/task/active/l2-02-observation-snapshot/deploy_013_图像预处理ImagePreprocess.md` |
| 验收证据目录 | `DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/` |
| 允许查看的 diff / 日志 | `src/model_deploy/act/service/image_preprocess.py`、`src/model_deploy/act/tests/service/test_image_preprocess.py`、执行摘要、pytest 输出 |

## 2. 验收模式

`direct-local`：当前环境可直接运行 unit / mock 测试。

## 3. 必跑命令

```bash
python3 -m pytest src/model_deploy/act/tests/service/test_image_preprocess.py -v
```

如果命令无法运行（缺依赖等），必须解释原因并返回 `BLOCKED_ENV`。

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL 条件（全部满足）

- [ ] `image_preprocess.py` 存在于 `src/model_deploy/act/service/image_preprocess.py`。
- [ ] `preprocess_observation_image(image, image_config)` 函数存在。
- [ ] 合法 RGB (H, W, 3) uint8 → resize/dtype 转换 → 输出符合 config 指定 shape/dtype。
- [ ] 不支持 image shape 时抛 ValueError。
- [ ] 不支持 image dtype 时抛 ValueError。
- [ ] 纯函数：无副作用，不修改输入 image。
- [ ] 无 ROS import，service 层在无 ROS 环境下可 import 和单测。
- [ ] pytest 全部通过，无 skip。
- [ ] 产物路径与 L3 声明一致。
- [ ] 未修改 types/observation.py、service/observation_collector.py、runtime/、ui/ 或 pi05/。

### FAIL_LOCAL 条件（任一命中）

- 上述 PASS 条件任一不满足。
- `preprocess_observation_image` 嵌入了 ROS message 解码逻辑。
- 不支持的 shape/dtype 静默通过（未抛异常）。
- 函数修改了输入 image（非纯函数）。
- 修改了禁止修改的文件。
- pytest 失败或有未解释的 skip。

### BLOCKED_ENV

- 缺少 Python3 或 pytest，无法运行测试。

## 5. 本 L3 是否影响 L2 Gate

| 字段 | 内容 |
|---|---|
| 影响 L2 Gate | 是 |
| 对应场景 | S3 图像预处理 |
| 贡献 | 将 ui 层 decode 后的 RGB 图像按 image config 转换为模型消费格式 |
| 仍需后续 L3 | deploy_005 ROS adapter 的 decode → preprocess 调用链路、deploy_006 端到端集成验证 |

## 6. 验收结论写入位置

```text
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-02-observation-snapshot/logs/deploy_013_acceptance_round_<n>.md
```

结论格式：

```text
结论：PASS_LOCAL / FAIL_LOCAL / BLOCKED_ENV / DEFER_TO_L2_GATE
检查项逐条结果：
- ...
反馈说明：
```
