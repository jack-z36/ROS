# <small>nlohmann::basic_json::</small>cbor_tag_handler_t

```cpp
enum class cbor_tag_handler_t
{
    error,
    ignore,
    store
};
```

This enumeration is used in the [`from_cbor`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/from_cbor.md) function to choose how to treat tags:

error
:   throw a `parse_error` exception in case of a tag

ignore
:   ignore tags

store
:   store tagged values as binary container with subtype (for bytes 0xd8..0xdb)

## Examples

??? example

    The example below shows how the different values of the `cbor_tag_handler_t` influence the behavior of
    [`from_cbor`](from_cbor.md) when reading a tagged byte string.

    ```cpp
    --8<-- "examples/cbor_tag_handler_t.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/cbor_tag_handler_t.output"
    ```

## Version history

- Added in version 3.9.0. Added value `store` in 3.10.0.
