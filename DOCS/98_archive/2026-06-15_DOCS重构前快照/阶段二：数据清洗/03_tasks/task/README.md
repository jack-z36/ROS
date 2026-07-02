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
task/completed/<L1归档目录>/<功能组>/
```

`<L1归档目录>` 固定使用：

- Runtime MVP：`01-runtime/`
- Service 场景一：`02-service-s1/`
- Service 场景二：`03-service-s2/`
- Service 场景三：`04-service-s3/`
- Service 场景四：`05-service-s4/`
- Service 场景五：`06-service-s5/`

完成移动后，如果原 `task/active/<功能组>/` 已经没有任何任务文件或其他保留文件，必须删除该空目录。
