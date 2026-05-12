# <small>nlohmann::basic_json::</small>json_serializer

```cpp
template<typename T, typename SFINAE>
using json_serializer = JSONSerializer<T, SFINAE>;
```

## Template parameters

`T`
:   type to convert; will be used in the `to_json`/`from_json` functions

`SFINAE`
:   type to add compile type checks via SFINAE; usually `#!cpp void`

## Notes

#### Default type

The default values for `json_serializer` is [`adl_serializer`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/adl_serializer/index.md).

## Examples

??? example

    The example below shows how a conversion of a non-default-constructible type is implemented via a specialization of
    the `adl_serializer`.
        
    ```cpp
    --8<-- "examples/from_json__non_default_constructible.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/from_json__non_default_constructible.output"
    ```

## Version history

- Since version 2.0.0.
