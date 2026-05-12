# <small>nlohmann::basic_json::</small>empty

```cpp
bool empty() const noexcept;
```

Checks if a JSON value has no elements (i.e., whether its [`size()`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/size.md) is `0`).
    
## Return value

The return value depends on the different types and is defined as follows:

| Value type | return value                           |
|------------|----------------------------------------|
| null       | `#!cpp true`                           |
| boolean    | `#!cpp false`                          |
| string     | `#!cpp false`                          |
| number     | `#!cpp false`                          |
| binary     | `#!cpp false`                          |
| object     | result of function `object_t::empty()` |
| array      | result of function `array_t::empty()`  |

## Exception safety

No-throw guarantee: this function never throws exceptions.

## Complexity

Constant, as long as [`array_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/array_t.md) and [`object_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/object_t.md) satisfy the
[Container](https://en.cppreference.com/w/cpp/named_req/Container) concept; that is, their `empty()` functions have
constant complexity.

## Possible implementation

```cpp
bool empty() const noexcept
{
    return size() == 0;
}
```

## Notes

This function does not return whether a string stored as JSON value is empty -- it returns whether the JSON container
itself is empty which is `#!cpp false` in the case of a string.

## Examples

??? example

    The following code uses `empty()` to check if a JSON object contains any elements.
    
    ```cpp
    --8<-- "examples/empty.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/empty.output"
    ```

## Version history

- Added in version 1.0.0.
- Extended to return `#!cpp false` for binary types in version 3.8.0.
