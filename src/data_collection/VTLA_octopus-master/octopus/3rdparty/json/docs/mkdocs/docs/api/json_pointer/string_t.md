# <small>nlohmann::json_pointer::</small>string_t
```cpp
using string_t = RefStringType;
```

The string type used for the reference tokens making up the JSON pointer.

See [`basic_json::string_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/string_t.md) for more information.

## Examples

??? example

    The example shows the type `string_t` and its relation to `basic_json::string_t`.
     
    ```cpp
    --8<-- "examples/json_pointer__string_t.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/json_pointer__string_t.output"
    ```

## Version history

- Added in version 3.11.0.
