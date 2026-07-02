# L3 微元任务：落地 frame_alignment 配置契约

## 1. 任务定位

阶段：阶段二：数据清洗
场景：场景一：提取夹爪开合以及位姿转换
L1：service_s1
L2 能力：位姿转换配置生成
L3 编号：service_s1_004
当前任务文件路径：`DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s1-g4/service_s1_004_落地frame_alignment配置契约.md`
任务类别：数据计算类
来源 L2 文件：`DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/位姿转换配置生成.md`

## 2. 本次目标

```text
让配置加载层支持 frame_alignment，明确 common_from_right_start 来自 T_right_start_common 求逆，并统一 camera_from_*_tcp 外参字段方向。
```

## 3. 本次不做

- 不改 MCAP 写出。
- 不改 calibration wizard 页面。
- 不实现统一 `--dev` 一级入口。

## 4. 执行对象

- `src/data_clean/config/mcap_process_config.py`
- `config/data_clean/*.yaml`
- [[FrameAlignmentConfig]]
- [[CameraFromTcpExtrinsic]]

## 5. 执行依赖

- g1 已定义 `FrameAlignmentConfig` 和 `CameraFromTcpExtrinsic`。
- 旧配置中可能仍存在 `start_from_common`。
- L2 已明确默认 `common_anchor = left`，`common_from_right_start = inverse(T_right_start_common)`。

## 6. 上游接口确认

```text
本 L3 直接依赖的上游功能：现有场景一配置加载
上游接口定义位置：src/data_clean/config/mcap_process_config.py；config/data_clean/
当前 L3 期望消费的字段 / 文件 / 返回值：common_anchor、pose_streams、T_right_start_common 的配置生成来源、common_from_left_start、common_from_right_start、camera_from_left_tcp、camera_from_right_tcp
是否存在接口冲突：旧配置使用 start_from_common，旧文档曾使用方向含混的 tcp_from_camera，并可能误写成固定底座直接给出 common_from_right_start
如果有冲突，本次处理策略：新契约统一为 frame_alignment + camera_from_*_tcp；common_from_right_start 语义必须是 inverse(T_right_start_common) 的结果；旧配置只能迁移或明确拒绝
```

## 7. 预期改动形态

- 配置加载能读取和校验 `frame_alignment`。
- 默认 `common_anchor: left`。
- `common_from_left_start` 默认为单位变换。
- `common_from_right_start` 文档和配置注释必须标明由 `T_right_start_common` 求逆生成。
- 非法 anchor、非法四元数、缺外参能给出明确错误。
- dev 检验项可生成配置校验摘要。

## 8. 现有程序盘点

- `mcap_process_config.py` 已有 `TransformConfig`、`PoseStreamConfig`、`GripperStreamConfig` 和 cross-field 校验。
- 当前位姿配置仍围绕 `pose_streams + transform_file + start_from_common`。
- 现有风险是旧 transform 方向与新 `common_from_*_start` 命名不同，不能静默改名。
- 新算法中 `common_from_right_start` 不是固定底座直接给出的外参，而是右手处于 common frame 标定位姿时的 raw pose `T_right_start_common` 的逆。

## 9. 本 L3 的真实改造边界

- 只改配置模型、配置模板和配置校验。
- 不做位姿矩阵计算输出。
- 不修改浏览器配置生成器；该任务由 service_s1_005 承接。

## 10. 计算输出

### 计算规则

| 输入情况 | 计算 / 判断规则 | 预期输出 | reason / error |
|---|---|---|---|
| 合法输入 | `common_anchor` 为 `left/right` 且外参完整 | 配置加载成功 | 无 |
| 缺失输入 | 缺 `frame_alignment` 必填字段 | 配置加载失败 | missing field |
| 边界输入 | `common_anchor: left` 但 `common_from_left_start` 非单位 | 配置加载失败 | anchor identity mismatch |
| 标定来源 | `common_anchor: left` 且存在 `T_right_start_common` 来源说明 | `common_from_right_start` 语义为其逆 | calibration pose inverse |

### 输出结构

| 字段 | 类型 | 含义 | 有效性要求 |
|---|---|---|---|
| `common_anchor` | enum | common frame 锚点 | `left/right` |
| `common_from_*_start` | SE(3) | start frame 到 common frame 外参 | 四元数 xyzw |
| `camera_from_*_tcp` | SE(3) | TCP 在 camera frame 下的外参 | 表示 `T_camera_tcp` |
| `T_right_start_common` 来源 | metadata / dev summary | 右手标定采样 raw pose | 不进入每帧输出，但必须可追溯 |

## 11. 数据计算验收重点

- 合法输入通过。
- 缺失或非法输入失败。
- 错误信息能说明具体缺口。
- 输出结构可被下游直接消费。
- 配置注释或摘要能说明 `common_from_right_start = inverse(T_right_start_common)`。

## 12. 开发者验收入口

`./start_data_clean.sh --dev -> 场景一 -> scene1_frame_alignment_config`

本 L3 负责该检验项中的“配置加载与校验”部分。测试产物：`artifacts/frame_alignment_summary.json`、`logs/run_log.json`。

## 13. 必读上下文

### 必读任务文档

1. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2能力模块/位姿转换配置生成.md`
2. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/FrameAlignmentConfig.md`
3. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/L2数据定义/CameraFromTcpExtrinsic.md`

### 必读相关微元任务记录

1. `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s1-g1/service_s1_001_稳定cleaned_MCAP接口契约.md`

如果没有找到已完成相关 L3 历史记录，执行摘要中必须明确写明“未找到相关 L3 历史记录”。

### 必读约束文档

1. `DOCS/02_约束/阶段二任务体系/L3编码执行原则.md`
2. `DOCS/02_约束/阶段二任务体系/L3任务文件身份校验约束.md`
3. `DOCS/02_约束/阶段二任务体系/L3执行TDD与归档约束.md`
4. `DOCS/02_约束/阶段二任务体系/功能分支接力流程.md`
5. `DOCS/02_约束/阶段二任务体系/L3功能组目录约束.md`
6. `DOCS/02_约束/阶段二任务体系/上游依赖接口对齐约束.md`
7. `DOCS/02_约束/阶段二任务体系/文件存放规范.md`
8. `DOCS/02_约束/阶段二任务体系/L3现有实现盘点约束.md`
9. `DOCS/03_工程/阶段二：数据清洗/02_service/场景一/执行约束.md`

### 必读代码

1. `src/data_clean/config/mcap_process_config.py`
2. `config/data_clean/`

## 14. TDD 执行要求

执行前必须先完成 L3 任务文件身份校验。本 L3 涉及代码行为变更，必须先读取并使用 `$tdd`。

```text
$tdd
```

## 15. 允许修改

- `src/data_clean/config/`
- `src/data_clean/tests/`
- `config/data_clean/`
- 当前 L3 任务文件自身

## 16. 禁止修改

- 禁止修改 MCAP 写出策略。
- 禁止继续混用 `tcp_from_camera`。
- 禁止把 `common_from_right_start` 写成固定底座直接给出。
- 禁止新增桌面 `origin_frame` 作为默认方案。

## 17. 验收命令

```bash
python3 -m pytest src/data_clean/tests/config -q
```

## 18. 成功标准

- [ ] `frame_alignment` 合法配置加载通过。
- [ ] 非法 `common_anchor` 会失败。
- [ ] `camera_from_*_tcp` 方向语义有测试覆盖。
- [ ] `common_from_right_start` 来源语义明确为 `inverse(T_right_start_common)`。
- [ ] dev 检验项配置校验产物契约明确。

## 19. 完成后交接

必须更新当前 L3 任务文件本身，追加执行摘要，并将当前 L3 移动到 `DOCS/03_工程/阶段二：数据清洗/03_tasks/task/completed/02-service-s1/service-s1-g4/`。移动后如果 active 功能组为空，删除该空目录。不写共享执行记录。

## 20. 执行摘要

### 任务文件身份校验

```text
用户指定路径：DOCS/03_工程/阶段二：数据清洗/03_tasks/task/active/service-s1-g4/service_s1_004_落地frame_alignment配置契约.md
实际读取路径：一致
文件名编号：service_s1_004
正文 L3 编号：service_s1_004
校验结论：通过
```

### 相关 L3 历史记录

未找到相关 L3 历史记录（本 L3 为 service-s1-g4 功能组首个执行任务）。

### TDD 执行过程

- **RED**: 创建 `src/data_clean/tests/config/test_frame_alignment_config.py`，16 个测试因 `ExtrinsicConfig`/`FrameAlignmentConfig` 不存在而导入失败。
- **GREEN**: 在 `src/data_clean/repo/config/mcap_process_config.py` 中实现 `ExtrinsicConfig`、`FrameAlignmentConfig` 数据类，`load_frame_alignment()`、`validate_frame_alignment()` 函数，更新 `AppConfig` 增加可选 `frame_alignment` 字段，更新 `load_app_config()` 加载逻辑。
- **Refactor**: 修复测试数据浅拷贝问题（改用 `copy.deepcopy`），修正 `load_frame_alignment` API 为接收完整 config dict。
- 所有 16 个测试通过，现有 29 个 service 测试无回归。

### 修改文件清单

1. `src/data_clean/repo/config/mcap_process_config.py`：新增 `ExtrinsicConfig`、`FrameAlignmentConfig` 数据类，`load_frame_alignment()`、`validate_frame_alignment()` 函数，`AppConfig` 增加 `frame_alignment` 可选字段。
2. `src/data_clean/config/mcap_process_config.py`：更新 re-export，新增 `ExtrinsicConfig`、`FrameAlignmentConfig`、`load_frame_alignment`、`validate_frame_alignment`。
3. `src/data_clean/tests/config/test_frame_alignment_config.py`：新增 16 个测试，覆盖数据类、加载、校验、集成。
4. `config/data_clean/data_clean_smoke_test.yaml`：新增 `frame_alignment` 配置段及注释。
5. `config/data_clean/data_clean_calibrated.yaml`：新增 `frame_alignment` 配置段及注释。

### 新增/修改函数

- `ExtrinsicConfig.identity()` / `.from_dict()` / `.is_identity()` / `.quaternion_norm()`
- `FrameAlignmentConfig.from_dict()`
- `load_frame_alignment(data)` → `FrameAlignmentConfig`
- `validate_frame_alignment(config)` → None (raises ConfigError on invalid)
- `AppConfig.frame_alignment: FrameAlignmentConfig | None`

### 验收命令结果

```bash
python3 -m pytest src/data_clean/tests/config -q
# 16 passed in 0.03s

python3 -m pytest src/data_clean/tests/service -q
# 29 passed in 0.37s (no regression)
```

### 成功标准勾选

- [x] `frame_alignment` 合法配置加载通过。
- [x] 非法 `common_anchor` 会失败。
- [x] `camera_from_*_tcp` 方向语义有测试覆盖。
- [x] `common_from_right_start` 来源语义明确为 `inverse(T_right_start_common)`（配置注释和文档明确标明）。
- [x] dev 检验项配置校验产物契约明确（`load_frame_alignment` + `validate_frame_alignment` 可被 `scene1_frame_alignment_config` 检验项调用）。

### 对开发者验收入口的影响

本 L3 为 `./start_data_clean.sh --dev -> 场景一 -> scene1_frame_alignment_config` 检验项提供配置加载与校验基础。后续 `service_s1_005` 将改造位姿转换配置生成器，本 L3 提供的 `load_frame_alignment` 和 `validate_frame_alignment` 可被该检验项直接调用。

### 明确没做什么

- 不改 MCAP 写出。
- 不改 calibration wizard 页面。
- 不实现统一 `--dev` 一级入口。
- 不做位姿矩阵计算输出。

### 后续建议

建议用户后续运行 `./start_data_clean.sh --dev`，选择场景一的 `scene1_frame_alignment_config` 功能检验项做最终人工验收。
