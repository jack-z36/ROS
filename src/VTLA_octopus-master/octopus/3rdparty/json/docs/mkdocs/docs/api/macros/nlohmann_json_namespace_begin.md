# NLOHMANN_JSON_NAMESPACE_BEGIN, NLOHMANN_JSON_NAMESPACE_END

```cpp
#define NLOHMANN_JSON_NAMESPACE_BEGIN /* value */  // (1)
#define NLOHMANN_JSON_NAMESPACE_END   /* value */  // (2)
```

These macros can be used to open and close the `nlohmann` namespace. See
[`nlohmann` Namespace](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/features/namespace.md#structure) for details.

1. Opens the namespace.
2. Closes the namespace.

## Default definition

The default definitions open and close the `nlohmann` namespace. The precise definition of
[`NLOHMANN_JSON_NAMESPACE_BEGIN`] varies as described [here](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/features/namespace.md#structure).

1. Default definition of `NLOHMANN_JSON_NAMESPACE_BEGIN`:

    ```cpp
    namespace nlohmann
    {
    inline namespace json_abi_v3_11_2
    {
    ```

2. Default definition of `NLOHMANN_JSON_NAMESPACE_END`:
    ```cpp
    }  // namespace json_abi_v3_11_2
    }  // namespace nlohmann
    ```

When these macros are not defined, the library will define them to their default definitions.

## Examples

??? example

    The example shows how to use `NLOHMANN_JSON_NAMESPACE_BEGIN`/`NLOHMANN_JSON_NAMESPACE_END` from the
    [How do I convert third-party types?](../../features/arbitrary_types.md#how-do-i-convert-third-party-types) page.

    ```cpp
    --8<-- "examples/nlohmann_json_namespace_begin.c++17.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/nlohmann_json_namespace_begin.c++17.output"
    ```

## See also

- [`nlohmann` Namespace](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/features/namespace.md)
- [NLOHMANN_JSON_NAMESPACE](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_json_namespace.md)
- [`NLOHMANN_JSON_NAMESPACE_NO_VERSION`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_json_namespace_no_version.md)

## Version history

- Added in version 3.11.0. Changed inline namespace name in version 3.11.2.
