# repo 层设计：L2-06

本 L2 不在该层新增源码产物。

原因：ControlLoop 不读取 bundle、文件、网络或硬件资源。模型/bundle 的进程外读取由 L2-03 repo，ROS/hardware 边界由 L2-05/UI 负责。

验收如何确认：runtime 单测以 fake worker/guard/publisher 运行；`control_loop.py` 不 import ROS、文件系统或 policy loader。

层职责：把进程外资源读入 RAM；本 L2 不具备该职责。输入输出和副作用均无。本文件任务边界继承当前 L1/L2 功能边界，不来自旧 layer-based L2 卡片。Pi0.5 参考：旧 `ControlLoop` 只经 queue/回调拿 RAM 对象。
