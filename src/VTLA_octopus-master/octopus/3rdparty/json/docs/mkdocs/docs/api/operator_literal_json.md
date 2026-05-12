# <small>nlohmann::</small>operator""_json

```cpp
json operator ""_json(const char* s, std::size_t n);
json operator ""_json(const char8_t* s, std::size_t n);  // since C++20
```

This operator implements a user-defined string literal for JSON objects. It can be used by adding `#!cpp _json` to a
string literal and returns a [`json`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/json.md) object if no parse error occurred.

It is recommended to bring the operator into scope using any of the following lines:
```cpp
using nlohmann::literals::operator ""_json;
using namespace nlohmann::literals;
using namespace nlohmann::json_literals;
using namespace nlohmann::literals::json_literals;
using namespace nlohmann;
```

This is suggested to ease migration to the next major version release of the library. See
[`JSON_USE_GLOBAL_UDLS`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_use_global_udls.md#notes) for details.

## Parameters

`s` (in)
:   a string representation of a JSON object

`n` (in)
:   length of string `s`

## Return value

[`json`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/json.md) value parsed from `s`

## Exceptions

The function can throw anything that [`parse(s, s+n)`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/parse.md) would throw.

## Complexity

Linear.

## Examples

??? example

    The following code shows how to create JSON values from string literals.
     
    ```cpp
    --8<-- "examples/operator_literal_json.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/operator_literal_json.output"
    ```

## Version history

- Added in version 1.0.0.
- Moved to namespace `nlohmann::literals::json_literals` in 3.11.0.
- Added `char8_t*` overload in 3.12.1.
