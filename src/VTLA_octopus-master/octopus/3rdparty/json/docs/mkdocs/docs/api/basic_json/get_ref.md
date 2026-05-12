# <small>nlohmann::basic_json::</small>get_ref

```cpp
template<typename ReferenceType>
ReferenceType get_ref();

template<typename ReferenceType>
const ReferenceType get_ref() const;
```

Implicit reference access to the internally stored JSON value. No copies are made.

## Template parameters

`ReferenceType`
:   reference type; must be a reference to [`array_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/array_t.md), [`object_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/object_t.md),
    [`string_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/string_t.md), [`boolean_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/boolean_t.md), [`number_integer_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/number_integer_t.md), or
    [`number_unsigned_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/number_unsigned_t.md), [`number_float_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/number_float_t.md), or [`binary_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/binary_t.md).
    Enforced by a static assertion.

## Return value

reference to the internally stored JSON value if the requested reference type fits to the JSON value; throws
[`type_error.303`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/home/exceptions.md#jsonexceptiontype_error303) otherwise

## Exception safety

Strong exception safety: if an exception occurs, the original value stays intact.

## Exceptions

Throws [`type_error.303`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/home/exceptions.md#jsonexceptiontype_error303) if the requested reference type does not
match the stored JSON value type; example: `"incompatible ReferenceType for get_ref, actual type is binary"`.

## Complexity

Constant.

## Notes

!!! danger "Undefined behavior"

    The reference becomes invalid if the underlying JSON object changes.

## Examples

??? example

    The example shows several calls to `get_ref()`.
    
    ```cpp
    --8<-- "examples/get_ref.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/get_ref.output"
    ```

## See also

- [get_ptr()](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/get_ptr.md) get a pointer value

## Version history

- Added in version 1.1.0.
- Extended to binary types in version 3.8.0.
