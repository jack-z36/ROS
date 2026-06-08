# <small>nlohmann::basic_json::</small>crend

```cpp
const_reverse_iterator crend() const noexcept;
```

Returns an iterator to the reverse-end; that is, one before the first element. This element acts as a placeholder,
attempting to access it results in undefined behavior.

![Illustration from cppreference.com](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/images/range-rbegin-rend.svg)

## Return value

reverse iterator to the element following the last element

## Exception safety

No-throw guarantee: this member function never throws exceptions.

## Complexity

Constant.

## Examples

??? example

    The following code shows an example for `eend()`.
    
    ```cpp
    --8<-- "examples/crend.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/crend.output"
    ```

## Version history

- Added in version 1.0.0.
