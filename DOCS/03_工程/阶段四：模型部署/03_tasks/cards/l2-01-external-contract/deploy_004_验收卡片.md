# 验收卡片：deploy_004 manifest 解析器

> [!info] 归属
> - L2：l2-01-external-contract（外部参数加载与契约校验闭环）
> - L3：deploy_004 manifest 解析器
> - 验收模式：direct-local
> - 验收轮次上限：3
> - Pi0.5 参考源码：只读，不得修改

## 1. 检查对象

| 检查项 | 路径 | 类型 | 说明 |
|---|---|---|---|
| 源码 | `src/model_deploy/act/repo/manifest_parser.py` | 新建 | manifest 解析器实现 |
| 测试 | `src/model_deploy/act/tests/repo/test_manifest_parser.py` | 新建 | 单元测试（正常/缺文件/坏 JSON） |

## 2. 验收模式

direct-local：在本地直接运行 pytest 进行验收，不依赖真机环境，不依赖外部服务。验收轮次上限为 3，第一轮失败后可在第二轮修正后重新验收。

## 3. 必跑命令

```bash
cd /home/hit/ROS/worktrees/l2-01
python -m pytest src/model_deploy/act/tests/repo/test_manifest_parser.py -v --tb=short
```

## 4. PASS / FAIL / BLOCKED 判断标准

### PASS_LOCAL

满足以下全部条件则判定为 PASS_LOCAL：

- pytest 退出码为 0，全部用例通过（正常解析、缺文件、坏 JSON 三个用例）。
- 正常路径用例：传入含合法 manifest.json 的目录，返回 dict 内容与文件内容一致。
- 缺文件用例：传入不含 manifest.json 的目录，抛出 `FileNotFoundError`。
- 坏 JSON 用例：传入含损坏 manifest.json 的目录，抛出 `json.JSONDecodeError`。
- 源码静态检查：`manifest_parser.py` 中无 config/service/runtime/ui 层 import。
- 源码静态检查：无维度硬编码（26/14），无 blend_steps/smoothstep/cross_chunk/rtc_alignment/action_smoothing。
- 源码静态检查：无 schema 版本校验或字段完备性校验（仅文件读取 + JSON 解析）。
- 未修改任何越界文件（types/config/service/runtime/ui 层、Pi0.5 源码、其他 L3 产物）。

### FAIL_LOCAL

满足以下任一条件则判定为 FAIL_LOCAL：

- pytest 退出码非 0，存在失败用例。
- 正常路径用例返回 dict 内容与预期不符。
- 缺文件场景未抛出 `FileNotFoundError`（如静默返回空 dict 或吞掉异常）。
- 坏 JSON 场景未抛出 `json.JSONDecodeError`（如被捕获后返回默认值）。
- 源码包含越界 import（config/service/runtime/ui 层）。
- 源码包含维度硬编码或 action 平滑相关逻辑。
- 修改了越界文件。

### BLOCKED_ENV

满足以下任一条件则判定为 BLOCKED_ENV（不计入验收轮次）：

- depends_on（deploy_001/002/003）未完成，导致无法执行。
- Python 环境或 pytest 不可用（环境问题，非代码问题）。
- 分支或工作区状态异常（非本 L3 代码导致）。
- BLOCKED_ENV 需在验收日志中注明阻塞原因，解决后可不计入轮次重新验收。

## 5. 本 L3 是否影响 L2 Gate

| L2 Gate | 场景描述 | 本 L3 是否影响 | 影响方式 |
|---|---|---|---|
| S3 | bundle 缺文件失败 | 是（核心支撑） | manifest 缺文件时抛出 `FileNotFoundError`，使 S3 场景可被上层捕获并报错 |
| S4 | normalizer 维度不一致失败 | 否 | 归 deploy_005 加载 + deploy_009 校验 |

## 6. 验收结论写入位置

验收结论写入路径：

```
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/deploy_004_验收结论.md
```

格式要求：

```text
task_id: deploy_004
验收轮次: <1|2|3>
验收结果: <PASS_LOCAL|FAIL_LOCAL|BLOCKED_ENV>
验收日期: YYYY-MM-DD
pytest 退出码: <0|1|...>
用例总数: <N>
通过数: <N>
失败数: <N>
失败用例列表:（无则填「无」）
  - <case_name>: <失败原因>
阻塞原因:（PASS/FAIL 则填「无」）
验收人: <agent_id>
备注: <补充说明>
```

pytest 完整输出保存至：

```
DOCS/03_工程/阶段四：模型部署/05_acceptance/l2-01-external-contract/logs/deploy_004_round_<N>.txt
```
