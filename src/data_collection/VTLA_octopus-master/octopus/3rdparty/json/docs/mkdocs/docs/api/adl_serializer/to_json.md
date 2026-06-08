# <small>nlohmann::adl_serializer::</small>to_json

```cpp
template<typename BasicJsonType, typename TargetType = ValueType>
static auto to_json(BasicJsonType& j, TargetType && val) noexcept(
    noexcept(::nlohmann::to_json(j, std::forward<TargetType>(val))))
-> decltype(::nlohmann::to_json(j, std::forward<TargetType>(val)), void())
```

This function is usually called by the constructors of the [basic_json](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/index.md) class.

## Parameters

`j` (out)
:   JSON value to write to

`val` (in)
:   value to read from

## Examples

??? example

    The example below shows how a `to_json` function can be implemented for a user-defined type. This function is called
    by the `adl_serializer` when the constructor `basic_json(ns::person)` is called.
        
    ```cpp
    --8<-- "examples/to_json.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/to_json.output"
    ```

## See also

- [from_json](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/adl_serializer/from_json.md)

## Version history

- Added in version 2.1.0.
