# task 功能组任务池

本目录保存尚未完成的 L3 微元任务。L3 不直接放在本目录根部，必须按来源 L2 功能模块分组：

```text
task/active/<功能组>/<L3任务文件>.md
```

示例：

```text
task/active/runtime-g1/runtime_mvp_001_定义Runtime上下文Types.md
task/active/service-s1-g1/service_s1_001_xxx.md
```

同一个 L2 功能模块拆出的所有 L3 必须放入同一个功能组目录。任务完成后，移动到：

```text
task/completed/<功能组>/
```
