# <small>nlohmann::basic_json::</small>crbegin

```cpp
const_reverse_iterator crbegin() const noexcept;
```

Returns an iterator to the reverse-beginning; that is, the last element.

![Illustration from cppreference.com](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/images/range-rbegin-rend.svg)

## Return value

reverse iterator to the first element

## Exception safety

No-throw guarantee: this member function never throws exceptions.

## Complexity

Constant.

## Examples

??? example

    The following code shows an example for `crbegin()`.
    
    ```cpp
    --8<-- "examples/crbegin.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/crbegin.output"
    ```

## Version history

- Added in version 1.0.0.
