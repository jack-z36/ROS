# to_string(basic_json)

```cpp
template <typename BasicJsonType>
std::string to_string(const BasicJsonType& j);
```

This function implements a user-defined to_string for JSON objects.

## Template parameters

`BasicJsonType`
:   a specialization of [`basic_json`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/index.md)

## Return value

string containing the serialization of the JSON value

## Exception safety

Strong guarantee: if an exception is thrown, there are no changes to any JSON value.

## Exceptions

Throws [`type_error.316`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/home/exceptions.md#jsonexceptiontype_error316) if a string stored inside the JSON value
is not UTF-8 encoded

## Complexity

Linear.

## Possible implementation

```cpp
template <typename BasicJsonType>
std::string to_string(const BasicJsonType& j)
{
    return j.dump();
}
```

## Examples

??? example

    The following code shows how the library's `to_string()` function integrates with others, allowing
    argument-dependent lookup.
     
    ```cpp
    --8<-- "examples/to_string.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/to_string.output"
    ```

## See also

- [dump](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/dump.md)

## Version history

Added in version 3.7.0.
