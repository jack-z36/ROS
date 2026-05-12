# <small>nlohmann::basic_json::</small>default_object_comparator_t

```cpp
using default_object_comparator_t = std::less<StringType>;  // until C++14

using default_object_comparator_t = std::less<>;            // since C++14
```

The default comparator used by [`object_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/object_t.md).

Since C++14 a transparent comparator is used which prevents unnecessary string construction
when looking up a key in an object.

The actual comparator used depends on [`object_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/object_t.md) and can be obtained via
[`object_comparator_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/object_comparator_t.md).

## Examples

??? example

    The example below demonstrates the default comparator.

    ```cpp
    --8<-- "examples/default_object_comparator_t.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/default_object_comparator_t.output"
    ```

## Version history

- Added in version 3.11.0.
