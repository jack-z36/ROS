# std::swap<basic_json\>

```cpp
namespace std {
    void swap(nlohmann::basic_json& j1, nlohmann::basic_json& j2);
}
```

Exchanges the values of two JSON objects.

## Parameters

`j1` (in, out)
:   value to be replaced by `j2`

`j2` (in, out)
:   value to be replaced by `j1`

## Possible implementation

```cpp
void swap(nlohmann::basic_json& j1, nlohmann::basic_json& j2)
{
    j1.swap(j2);
}
```

## Examples

??? example

    The following code shows how two values are swapped with `std::swap`.
     
    ```cpp
    --8<-- "examples/std_swap.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/std_swap.output"
    ```

## See also

- [swap](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/swap.md)

## Version history

- Added in version 1.0.0.
- Extended for arbitrary basic_json types in version 3.10.5.
