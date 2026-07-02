# Service 处理能力模型

## 定位

Service 负责阶段二的业务处理能力。它消费 Repo 读取的数据和 Config 提供的参数，输出新的数据产物、报告或中间结果。

Service 不负责 UI 展示、任务调度、run 目录生命周期或用户交互。

## 宏观能力域

阶段二 Service 能力可以从宏观上分为：

- 清洗与基础校验：读取 raw MCAP，校验 topic/schema，写出 cleaned MCAP。
- 夹爪与位姿派生：提取夹爪宽度，生成 TCP / arm-base pose。
- 可靠性处理：异常检测、修复、位姿滤波、触觉滤波。
- step 对齐：生成 step timeline，对齐图像、位姿、夹爪和触觉。
- 数据集桥接：从 aligned MCAP 构建 LeRobotDataset v3 所需的中间表示。
- 质量解释：整合 quality、inspect、alignment、gripper/tactile 和 feature contract，形成训练前体检摘要。

## 对文档生成的影响

生成 Service L2 能力模块时，应先明确该能力消费哪个阶段产物、输出哪个阶段产物或报告，再定义数据概念。不要从源码函数名反推业务边界。

## 详细内容

- Service 源码目录：`src/data_clean/service/`
- 阶段二 Service 工程文档：`DOCS/03_工程/阶段二：数据清洗/02_service/`
- L2 能力模块规则：`DOCS/02_约束/阶段二任务体系/L2能力模块规则.md`
