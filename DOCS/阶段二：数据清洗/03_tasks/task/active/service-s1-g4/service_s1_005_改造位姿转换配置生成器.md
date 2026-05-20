# L3 微元任务：改造位姿转换配置生成器

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
功能组：service-s1-g4
L2 能力：位姿转换配置生成
L3 编号：service_s1_005
任务类别：工具对接类

## 2. 本次目标

```text
把已有 calibration wizard 的旧 common frame 配置写回，改造为 frame_alignment 配置生成。
```

## 3. 本次不做

- 不实现 pose 转换写出。
- 不生成夹爪配置。
- 不替用户推导真实底座外参。

## 4. 执行对象

- `src/data_clean/ui/mcap_calibration_wizard.py`
- `config/data_clean/data_clean_calibrated.yaml`
- `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/FrameAlignmentConfig.md`

## 5. 上游接口确认

```text
本 L3 直接依赖的上游功能：frame_alignment 配置加载
上游接口定义位置：DOCS/阶段二：数据清洗/03_tasks/task/active/service-s1-g4/service_s1_004_落地frame_alignment配置契约.md
当前 L3 期望消费的字段 / 文件 / 返回值：common_anchor、common_from_*_start、camera_from_*_tcp
是否存在接口冲突：旧向导写 start_from_common
如果有冲突，本次处理策略：新写出以 frame_alignment 为准，旧字段只作为迁移兼容或提示
```

## 6. 预期改动形态

- UI 或 CLI 支持选择 `common_anchor`，默认 `left`。
- 写出的配置包含 `frame_alignment.pose_streams` 和 `frame_alignment.extrinsics`。
- `common_from_left_start` 默认单位变换。
- `common_from_right_start` 可来自手工输入、CAD/测量值或标定采样。
- `camera_from_*_tcp` 可用单位占位，但必须标记来源。

## 7. 验收重点

- 生成配置能被 `service_s1_004` 的配置加载器读取。
- 切换 anchor 时不会只改字段名而不改外参方向。
- 终端摘要或 RAW_JSON 显示配置路径、anchor 和外参来源。

## 8. 必读上下文

1. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/位姿转换配置生成.md`
2. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/FrameAlignmentConfig.md`
3. `src/data_clean/ui/mcap_calibration_wizard.py`
4. `config/data_clean/data_clean_calibrated.yaml`

## 9. TDD 执行要求

执行前必须确认当前分支是 `service-s1`。本 L3 涉及代码行为和测试，必须先读取并使用 `$tdd`。

```text
$tdd
```

## 10. 允许修改

- `src/data_clean/ui/`
- `src/data_clean/config/`
- `src/data_clean/tests/`
- `config/data_clean/`
- 当前 L3 任务文件自身

## 11. 禁止修改

- 禁止新增桌面 `origin_frame` 作为默认方案。
- 禁止继续写出方向不明的 `start_from_common` 作为首选配置。
- 禁止改动 gripper 配置生成逻辑。

## 12. 验收命令

```bash
python3 -m pytest src/data_clean/tests -q
```

如浏览器 smoke test 依赖硬件，执行摘要必须说明，并至少完成配置写回单元测试。

## 13. 成功标准

- [ ] 配置生成默认 `common_anchor: left`。
- [ ] 输出包含 `common_from_left_start`、`common_from_right_start`。
- [ ] 输出包含 `camera_from_left_tcp`、`camera_from_right_tcp`。
- [ ] 生成配置能被加载器读取。

## 14. 完成后交接

必须更新当前 L3 文件、追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/service-s1-g4/`。
