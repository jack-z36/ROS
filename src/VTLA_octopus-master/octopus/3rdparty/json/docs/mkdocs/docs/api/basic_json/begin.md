# <small>nlohmann::basic_json::</small>begin

```cpp
iterator begin() noexcept;
const_iterator begin() const noexcept;
```

Returns an iterator to the first element.

![Illustration from cppreference.com](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/images/range-begin-end.svg)

## Return value

iterator to the first element

## Exception safety

No-throw guarantee: this member function never throws exceptions.

## Complexity

Constant.

## Examples

??? example

    The following code shows an example for `begin()`.
    
    ```cpp
    --8<-- "examples/begin.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/begin.output"
    ```

## Version history

- Added in version 1.0.0.
