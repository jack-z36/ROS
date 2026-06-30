# Pkg-config

If you are using bare Makefiles, you can use `pkg-config` to generate the include flags that point to where the library is installed:

```sh
pkg-config nlohmann_json --cflags
```

Users of the [Meson build system](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/integration/package_managers.md#meson) will also be able to use a system-wide library, which will be found by `pkg-config`:

```meson
json = dependency('nlohmann_json', required: true)
```
