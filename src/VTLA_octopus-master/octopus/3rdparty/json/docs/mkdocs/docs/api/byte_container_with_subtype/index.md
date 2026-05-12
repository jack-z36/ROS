# <small>nlohmann::</small>byte_container_with_subtype

```cpp
template<typename BinaryType>
class byte_container_with_subtype : public BinaryType;
```

This type extends the template parameter `BinaryType` provided to [`basic_json`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/index.md) with a subtype
used by BSON and MessagePack. This type exists so that the user does not have to specify a type themselves with a
specific naming scheme in order to override the binary type.

## Template parameters

`BinaryType`
:   container to store bytes (`#!cpp std::vector<std::uint8_t>` by default)

## Member types

- **container_type** - the type of the underlying container (`BinaryType`)
- **subtype_type** - the type of the subtype (`#!cpp std::uint64_t`)

## Member functions

- [(constructor)](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/byte_container_with_subtype/byte_container_with_subtype.md)
- **operator==** - comparison: equal
- **operator!=** - comparison: not equal
- [**set_subtype**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/byte_container_with_subtype/subtype.md) - sets the binary subtype
- [**subtype**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/byte_container_with_subtype/subtype.md) - return the binary subtype
- [**has_subtype**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/byte_container_with_subtype/has_subtype.md) - return whether the value has a subtype
- [**clear_subtype**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/byte_container_with_subtype/clear_subtype.md) - clears the binary subtype

## Version history

- Added in version 3.8.0.
- Changed the type of subtypes to `#!cpp std::uint64_t` in 3.10.0.
