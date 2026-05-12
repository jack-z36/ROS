# <small>nlohmann::basic_json::</small>is_number_float

```cpp
constexpr bool is_number_float() const noexcept;
```

This function returns `#!cpp true` if and only if the JSON value is a floating-point number. This excludes signed and
unsigned integer values.
    
## Return value

`#!cpp true` if type is a floating-point number, `#!cpp false` otherwise.

## Exception safety

No-throw guarantee: this member function never throws exceptions.

## Complexity

Constant.

## Examples

??? example

    The following code exemplifies `is_number_float()` for all JSON types.
    
    ```cpp
    --8<-- "examples/is_number_float.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/is_number_float.output"
    ```

## See also

- [is_number()](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_number.md) check if the value is a number
- [is_number_integer()](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_number_integer.md) check if the value is an integer or unsigned integer number
- [is_number_unsigned()](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_number_unsigned.md) check if the value is an unsigned integer number

## Version history

- Added in version 1.0.0.
