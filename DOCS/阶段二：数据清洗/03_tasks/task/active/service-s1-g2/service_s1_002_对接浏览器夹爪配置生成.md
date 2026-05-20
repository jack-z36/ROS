# L3 微元任务：对接浏览器夹爪配置生成

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
功能组：service-s1-g2
L2 能力：夹爪开合配置生成
L3 编号：service_s1_002
任务类别：工具对接类

## 2. 本次目标

```text
对接已有浏览器 GoPro 标定程序，使其稳定生成 GripperCalibrationConfig。
```

## 3. 本次不做

- 不实现 MCAP 夹爪宽度提取。
- 不修改 common frame 位姿配置。
- 不重写一套新的浏览器服务。

## 4. 执行对象

- `src/data_clean/ui/mcap_calibration_wizard.py`
- `config/data_clean/data_clean_calibrated.yaml`
- `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/GripperCalibrationConfig.md`

## 5. 上游接口确认

```text
本 L3 直接依赖的上游功能：GoPro live image 与现有浏览器标定向导
上游接口定义位置：src/data_clean/ui/mcap_calibration_wizard.py
当前 L3 期望消费的字段 / 文件 / 返回值：左右 GoPro 画面、网页点位/采样结果、YAML 写回配置
是否存在接口冲突：用户描述为点击两个点生成配置，现有代码可能是 ArUco 采样
如果有冲突，本次处理策略：优先复用现有 ArUco 采样；如缺点击点位能力，只补最小点位到配置写回链路
```

## 6. 预期改动形态

- 提供稳定终端入口启动浏览器标定。
- 左右手都能生成 `marker_id_*`、`marker_min`、`marker_max`、`gripper_max`。
- 输出字段归一到 `GripperCalibrationConfig`。
- 输出配置能被 `Scene1Config` 加载。

## 7. 验收重点

- 浏览器可显示左右 GoPro 视频画面。
- 完成标定后生成的 YAML 字段完整。
- `DATA_CLEAN_RAW_JSON=1` 或终端摘要能说明配置输出路径和左右手标定状态。

## 8. 必读上下文

1. `DOCS/阶段二：数据清洗/02_service/场景一/L2能力模块/夹爪开合配置生成.md`
2. `DOCS/阶段二：数据清洗/02_service/场景一/L2数据定义/GripperCalibrationConfig.md`
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

- 禁止修改 gripper width 提取算法。
- 禁止改变 gripper width 输出 topic 和消息类型。
- 禁止写入其他功能组目录。

## 12. 验收命令

```bash
python3 -m pytest src/data_clean/tests -q
```

如浏览器或硬件 smoke test 无法在当前环境执行，必须在执行摘要中说明，并至少完成配置写回单元测试。

## 13. 成功标准

- [ ] 已确认现有网页交互能力。
- [ ] 配置写回符合 `GripperCalibrationConfig`。
- [ ] 生成配置能被 `Scene1Config` 加载。

## 14. 完成后交接

必须更新当前 L3 文件、追加执行摘要，并移动到 `DOCS/阶段二：数据清洗/03_tasks/task/completed/service-s1-g2/`。
