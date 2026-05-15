# 阶段二 Service 工作入口

本目录承载阶段二五个业务 service 场景。进入任何 service 场景前，先阅读本目录任务级六件套，再阅读对应场景六件套。

## 必读顺序

1. `/home/hit/ROS/DOCS/public_rules.md`
2. `/home/hit/ROS/AGENTS.md`
3. `/home/hit/ROS/DOCS/阶段二：数据清洗/AGENTS.md`
4. `/home/hit/ROS/DOCS/阶段二：数据清洗/阶段目标描述.md`
5. `/home/hit/ROS/DOCS/阶段二：数据清洗/背景信息.md`
6. `/home/hit/ROS/DOCS/阶段二：数据清洗/当前进度.md`
7. `/home/hit/ROS/DOCS/阶段二：数据清洗/阶段产出.md`
8. 本目录六件套。
9. 具体场景六件套。

## 场景目录

- `场景一/`：提取夹爪开合以及位姿转换。
- `场景二/`：硬件数据可靠性验证。
- `场景三/`：MCAP 多 topic 时间轴对齐。
- `场景四/`：构建标准 canonical dataset。
- `场景五/`：模型训练格式导出器。

## 分层边界

Service 只实现业务处理能力，不管理 UI 交互菜单，不直接承担 Runtime 生命周期管理。Service 可以依赖 Types、Config 和 Repo，但不能依赖 Runtime 或 UI。
