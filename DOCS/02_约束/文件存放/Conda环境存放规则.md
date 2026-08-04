# Conda 环境存放规则

## 消费对象

Agent（涉及 Python、ROS、数据清洗、模型部署或其他 Conda 环境的创建、迁移、启动和验收时读取）。

## 权威性

本文是仓库关于 Conda 环境物理存放位置的全局权威约束。代码、脚本、阶段文档或历史执行记录与本文冲突时，以本文为准；历史记录只描述当时状态，不构成当前路径规则。

## 上游来源

本规则来自用户明确要求：Conda 环境必须放在 ROS 仓库目录之外，不受具体分支或 worktree 影响。

## 适用范围

适用于本 ROS 仓库及其所有分支、worktree、阶段工程和 Agent 创建或维护的全部 Conda 环境，包括数据清洗、模型部署、LeRobot 导出和后续新增环境。

## 核心规则

1. Conda 环境不得创建在 ROS 仓库目录及其子目录内。
2. Conda 环境不得创建在任何 Git worktree 内，包括 `worktrees/` 目录下的工作树。
3. 默认共享环境根目录为：

   ```text
   /home/hit/.conda-envs/
   ```

4. 环境目录必须使用与仓库路径无关的绝对路径。推荐结构：

   ```text
   /home/hit/.conda-envs/
   ├── data-clean/
   ├── lerobot-export/
   └── <其他环境>/
   ```

5. 环境目录属于机器级运行依赖，不进入 Git，不通过分支合并、复制源码或提交文件进行同步。
6. 所有启动脚本、systemd 单元、测试命令和运行时默认值必须引用共享环境路径，不能把当前 worktree 路径拼接为环境路径。
7. 如确需改变环境位置，必须通过明确的环境变量覆盖，而不是修改源码中的分支专属路径：

   | 环境变量 | 用途 | 默认值 |
   |---|---|---|
   | `DATA_CLEAN_ENV_ROOT` | 共享 Conda 环境根目录 | `/home/hit/.conda-envs` |
   | `DATA_CLEAN_CONDA_ENV` | data-clean 环境完整路径 | `${DATA_CLEAN_ENV_ROOT}/data-clean` |
   | `DATA_CLEAN_LEROBOT_ENV` | LeRobot 环境完整路径 | `${DATA_CLEAN_ENV_ROOT}/lerobot-export` |
   | `DATA_CLEAN_LEROBOT_PYTHON` | LeRobot 环境 Python 路径 | `${DATA_CLEAN_ENV_ROOT}/lerobot-export/bin/python` |

## 创建、迁移与验收

- 创建环境前，先确认目标路径不在 ROS 仓库或 worktree 内。
- 从旧仓库内路径迁移环境时，使用可恢复的目录移动；不得删除旧环境后再重建，除非用户明确授权。
- 迁移后必须验证：
  - 启动脚本能找到 `data-clean` Python；
  - 运行时能导入直接依赖；
  - 目标环境路径位于 ROS 仓库之外；
  - 代表性测试或项目规定的验收命令通过。
- 切换分支或 worktree 后，使用同一个共享环境路径重新执行上述验收，不得为每个分支复制一套 Conda 环境。

## 不负责范围

本文只约束 Conda 环境的物理存放位置、路径引用和迁移验收，不定义具体 Python 包版本、业务依赖、ROS 包构建规则或数据产物目录；这些内容由对应环境说明和阶段约束负责。

## 读取时机

创建、迁移、删除、启动、测试或修改任何 Conda 环境相关脚本前必须读取本文。

## 冲突处理

发现已有脚本或文档仍引用 ROS 仓库内环境路径时，先按本文修正当前权威脚本和约束；历史执行记录保留原样并视为历史事实。若目标机器、用户目录或环境迁移范围不明确，停止删除操作并请求确认。
