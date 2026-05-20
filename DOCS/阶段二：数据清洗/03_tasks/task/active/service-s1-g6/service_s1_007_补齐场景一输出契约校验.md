# L3 微元任务：补齐场景一输出契约校验

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
功能组：service-s1-g6
L2 能力：基础校验与输出契约检查
L3 编号：service_s1_007
任务类别：数据计算类

## 2. 本次目标

```text
补齐场景一输出 contract validator，使配置来源、raw pose、common pose、gripper topic 和失败原因都可被检查和报告。
```

## 3. 本次不做

- 不实现夹爪宽度算法。
- 不实现位姿转换算法。
- 不生成浏览器配置。

## 4. 执行对象

- `src/data_clean/service/validator.py`
- `src/data_clean/service/mcap_io.py`
- `src/data_clean/runtime/`
- `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1CleanReport.md`

## 5. 上游接口确认

```text
本 L3 直接依赖的上游功能：g2 夹爪配置生成、g3 夹爪宽度提取、g4 位姿配置生成、g5 common frame 位姿转换
上游接口定义位置：对应 L2 数据定义与 active/completed L3 记录
当前 L3 期望消费的字段 / 文件 / 返回值：config_path、raw_pose_count、camera_common_pose_count、tcp_common_pose_count、image_frame_count、gripper_count、failure_reason
是否存在接口冲突：若某个上游尚未实现，先用 fixture 或 mock 统计对象覆盖 validator 行为
如果有冲突，本次处理策略：本任务只做校验和报告，不反向改算法
```

## 6. 预期改动形态

- 缺 raw/image/pose topic 时失败原因可读。
- gripper output topic 与输入 topic 冲突时失败。
- raw pose、camera common pose、TCP common pose 数量不一致时失败。
- image frame 数与 gripper message 数不一致时失败。
- 报告或 RAW_JSON 摘要包含配置来源、common anchor、TCP 外参来源、插值帧统计。

## 7. 验收重点

- 合法输出 contract 通过。
- 每类缺失或冲突都有明确 failure reason。
- `DATA_CLEAN_RAW_JSON=1` 仍保持机器可读输出。
- `--dry-run --latest 1`、`--latest 1` 行为不倒退。

## 8. 必读上下文

1. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/基础校验与输出契约检查.md`
2. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/CleanedMcap.md`
3. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/Scene1CleanReport.md`
4. `src/data_clean/service/validator.py`
5. `src/data_clean/service/mcap_io.py`
6. `src/data_clean/runtime/`

## 9. TDD 执行要求

执行前必须确认当前分支是 `service-s1`。本 L3 涉及代码行为和测试，必须先读取并使用 `$tdd`。

```text
$tdd
```

## 10. 允许修改

- `src/data_clean/service/validator.py`
- `src/data_clean/service/mcap_io.py`
- `src/data_clean/runtime/`
- `src/data_clean/tests/`
- 当前 L3 任务文件自身

## 11. 禁止修改

- 禁止在本任务中修改 gripper 或 pose 计算算法。
- 禁止把报告文件写出扩展成 Runtime manifest 重构。
- 禁止写共享执行记录。

## 12. 验收命令

```bash
python3 -m pytest src/data_clean/tests/service -q
python3 -m pytest src/data_clean/tests/contract -q
```

## 13. 成功标准

- [ ] 合法输出 contract 通过。
- [ ] pose 数量不一致会失败。
- [ ] gripper 数量不一致会失败。
- [ ] topic 冲突会失败。
- [ ] RAW_JSON 输出仍可被解析。

## 14. 完成后交接

必须更新当前 L3 文件、追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/service-s1-g6/`。
