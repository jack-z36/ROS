# Macros

Some aspects of the library can be configured by defining preprocessor macros **before** including the `json.hpp`
header. See also the [macro overview page](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/features/macros.md).

## Runtime assertions

- [**JSON_ASSERT(x)**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_assert.md) - control behavior of runtime assertions

## Exceptions

- [**JSON_CATCH_USER(exception)**<br>**JSON_THROW_USER(exception)**<br>**JSON_TRY_USER**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_throw_user.md) - control exceptions
- [**JSON_DIAGNOSTICS**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_diagnostics.md) - control extended diagnostics
- [**JSON_DIAGNOSTIC_POSITIONS**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_diagnostic_positions.md) - access positions of elements
- [**JSON_NOEXCEPTION**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_noexception.md) - switch off exceptions

## Language support

- [**JSON_HAS_CPP_11**<br>**JSON_HAS_CPP_14**<br>**JSON_HAS_CPP_17**<br>**JSON_HAS_CPP_20**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_has_cpp_11.md) - set supported C++ standard
- [**JSON_HAS_FILESYSTEM**<br>**JSON_HAS_EXPERIMENTAL_FILESYSTEM**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_has_filesystem.md) - control `std::filesystem` support
- [**JSON_HAS_RANGES**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_has_ranges.md) - control `std::ranges` support
- [**JSON_HAS_THREE_WAY_COMPARISON**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_has_three_way_comparison.md) - control 3-way comparison support
- [**JSON_NO_IO**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_no_io.md) - switch off functions relying on certain C++ I/O headers
- [**JSON_SKIP_UNSUPPORTED_COMPILER_CHECK**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_skip_unsupported_compiler_check.md) - do not warn about unsupported compilers
- [**JSON_USE_GLOBAL_UDLS**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_use_global_udls.md) - place user-defined string literals (UDLs) into the global namespace

## Library version

- [**JSON_SKIP_LIBRARY_VERSION_CHECK**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_skip_library_version_check.md) - skip library version check
- [**NLOHMANN_JSON_VERSION_MAJOR**<br>**NLOHMANN_JSON_VERSION_MINOR**<br>**NLOHMANN_JSON_VERSION_PATCH**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_json_version_major.md)
  \- library version information

## Library namespace

- [**NLOHMANN_JSON_NAMESPACE**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_json_namespace.md) - full name of the `nlohmann` namespace
- [**NLOHMANN_JSON_NAMESPACE_BEGIN**<br>**NLOHMANN_JSON_NAMESPACE_END**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_json_namespace_begin.md) - open and
  close the library namespace
- [**NLOHMANN_JSON_NAMESPACE_NO_VERSION**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_json_namespace_no_version.md) - disable the version component of
  the inline namespace

## Type conversions

- [**JSON_DISABLE_ENUM_SERIALIZATION**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_disable_enum_serialization.md) - switch off default serialization/deserialization functions for enums
- [**JSON_USE_IMPLICIT_CONVERSIONS**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_use_implicit_conversions.md) - control implicit conversions

## Comparison behavior

- [**JSON_USE_LEGACY_DISCARDED_VALUE_COMPARISON**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_use_legacy_discarded_value_comparison.md) -
  control comparison of discarded values

## Serialization/deserialization macros

### Enums

- [**NLOHMANN_JSON_SERIALIZE_ENUM**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_json_serialize_enum.md) - serialize/deserialize an enum

### Classes and structs

- [**NLOHMANN_DEFINE_TYPE_INTRUSIVE**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_type_intrusive.md) - serialize/deserialize a non-derived class
  with private members
- [**NLOHMANN_DEFINE_TYPE_INTRUSIVE_WITH_DEFAULT**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_type_intrusive.md) - serialize/deserialize a
  non-derived class with private members; uses default values
- [**NLOHMANN_DEFINE_TYPE_INTRUSIVE_ONLY_SERIALIZE**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_type_intrusive.md) - serialize a non-derived class
  with private members
- [**NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_type_non_intrusive.md) - serialize/deserialize a non-derived
  class
- [**NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE_WITH_DEFAULT**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_type_non_intrusive.md) - serialize/deserialize a
  non-derived class; uses default values
- [**NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE_ONLY_SERIALIZE**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_type_non_intrusive.md) - serialize a
  non-derived class

- [**NLOHMANN_DEFINE_DERIVED_TYPE_INTRUSIVE**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_derived_type.md) - serialize/deserialize a derived class
  with private members
- [**NLOHMANN_DEFINE_DERIVED_TYPE_INTRUSIVE_WITH_DEFAULT**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_derived_type.md) - serialize/deserialize a
  derived class with private members; uses default values
- [**NLOHMANN_DEFINE_DERIVED_TYPE_INTRUSIVE_ONLY_SERIALIZE**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_derived_type.md) - serialize a derived
  class with private members
- [**NLOHMANN_DEFINE_DERIVED_TYPE_NON_INTRUSIVE**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_derived_type.md) - serialize/deserialize a derived
  class
- [**NLOHMANN_DEFINE_DERIVED_TYPE_NON_INTRUSIVE_WITH_DEFAULT**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_derived_type.md) - serialize/deserialize
  a derived class; uses default values
- [**NLOHMANN_DEFINE_DERIVED_TYPE_NON_INTRUSIVE_ONLY_SERIALIZE**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/nlohmann_define_derived_type.md) - serialize a derived
  class
