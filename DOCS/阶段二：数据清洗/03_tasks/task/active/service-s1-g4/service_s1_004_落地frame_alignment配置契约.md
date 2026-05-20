# L3 微元任务：落地 frame_alignment 配置契约

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
功能组：service-s1-g4
L2 能力：位姿转换配置生成
L3 编号：service_s1_004
任务类别：配置类

## 2. 本次目标

```text
将旧 pose_streams + transform_file + start_from_common 配置迁移为 frame_alignment 配置契约，并明确 TCP 外参字段方向。
```

## 3. 本次不做

- 不实现 MCAP pose 写出。
- 不改浏览器页面交互。
- 不执行 IK 或场景二处理。

## 4. 执行对象

- `src/data_clean/config/mcap_process_config.py`
- `config/data_clean/*.yaml`
- `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/FrameAlignmentConfig.md`
- `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/TcpFromCameraExtrinsic.md`

## 5. 上游接口确认

```text
本 L3 直接依赖的上游功能：现有配置加载和旧 transform YAML
上游接口定义位置：src/data_clean/config/mcap_process_config.py；config/data_clean/
当前 L3 期望消费的字段 / 文件 / 返回值：common_anchor、common_from_left_start、common_from_right_start、camera_from_left_tcp、camera_from_right_tcp
是否存在接口冲突：旧文档曾使用 tcp_from_camera 但公式需要 T_camera_tcp
如果有冲突，本次处理策略：字段统一为 camera_from_*_tcp，计算语义统一为 T_camera_tcp
```

## 6. 预期改动形态

- 配置模型能读取 `frame_alignment.common_anchor`，默认 `left`。
- 配置模型能读取 `common_from_left_start` 和 `common_from_right_start`。
- TCP 外参字段统一为 `camera_from_left_tcp`、`camera_from_right_tcp`，表示 `T_camera_tcp`。
- 旧 `start_from_common` 配置要么可迁移，要么明确失败并给出原因。

## 7. 验收重点

- `common_anchor: left` 时，`common_from_left_start` 必须是单位变换。
- `common_anchor` 非 `left/right` 时失败。
- 四元数顺序固定为 `xyzw`。
- 非单位四元数失败或被明确归一化。

## 8. 必读上下文

1. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/位姿转换配置生成.md`
2. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/FrameAlignmentConfig.md`
3. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/TcpFromCameraExtrinsic.md`
4. `src/data_clean/config/mcap_process_config.py`
5. `src/data_clean/service/tcp_transform.py`

## 9. TDD 执行要求

执行前必须确认当前分支是 `service-s1`。本 L3 涉及代码行为和测试，必须先读取并使用 `$tdd`。

```text
$tdd
```

## 10. 允许修改

- `src/data_clean/config/`
- `src/data_clean/tests/`
- `config/data_clean/`
- 当前 L3 任务文件自身

## 11. 禁止修改

- 禁止在本任务中修改 MCAP 写出策略。
- 禁止继续混用 `tcp_from_camera` 与 `camera_from_tcp`。
- 禁止新增桌面 `origin_frame` 作为默认方案。

## 12. 验收命令

```bash
python3 -m pytest src/data_clean/tests/config -q
```

## 13. 成功标准

- [ ] `frame_alignment` 新配置加载通过。
- [ ] 非法 `common_anchor` 会失败。
- [ ] TCP 外参字段方向与公式一致。
- [ ] 旧配置迁移或拒绝策略有测试覆盖。

## 14. 完成后交接

必须更新当前 L3 文件、追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/service-s1-g4/`。
