# <small>nlohmann::</small>basic_json

<small>Defined in header `<nlohmann/json.hpp>`</small>

```cpp
template<
    template<typename U, typename V, typename... Args> class ObjectType = std::map,
    template<typename U, typename... Args> class ArrayType = std::vector,
    class StringType = std::string,
    class BooleanType = bool,
    class NumberIntegerType = std::int64_t,
    class NumberUnsignedType = std::uint64_t,
    class NumberFloatType = double,
    template<typename U> class AllocatorType = std::allocator,
    template<typename T, typename SFINAE = void> class JSONSerializer = adl_serializer,
    class BinaryType = std::vector<std::uint8_t>,
    class CustomBaseClass = void
>
class basic_json;
```

## Template parameters

| Template parameter   | Description                                                               | Derived type                                |
|----------------------|---------------------------------------------------------------------------|---------------------------------------------|
| `ObjectType`         | type for JSON objects                                                     | [`object_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/object_t.md)                   |
| `ArrayType`          | type for JSON arrays                                                      | [`array_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/array_t.md)                     |
| `StringType`         | type for JSON strings and object keys                                     | [`string_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/string_t.md)                   |
| `BooleanType`        | type for JSON booleans                                                    | [`boolean_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/boolean_t.md)                 |
| `NumberIntegerType`  | type for JSON integer numbers                                             | [`number_integer_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/number_integer_t.md)   |
| `NumberUnsignedType` | type for JSON unsigned integer numbers                                    | [`number_unsigned_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/number_unsigned_t.md) |
| `NumberFloatType`    | type for JSON floating-point numbers                                      | [`number_float_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/number_float_t.md)       |
| `AllocatorType`      | type of the allocator to use                                              |                                             |
| `JSONSerializer`     | the serializer to resolve internal calls to `to_json()` and `from_json()` | [`json_serializer`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/json_serializer.md)     |
| `BinaryType`         | type for binary arrays                                                    | [`binary_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/binary_t.md)                   |
| `CustomBaseClass`    | extension point for user code                                             | [`json_base_class_t`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/json_base_class_t.md) |

## Specializations

- [**json**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/json.md) - default specialization
- [**ordered_json**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/ordered_json.md) - a specialization that maintains the insertion order of object keys

## Iterator invalidation

All operations that add values to an **array** ([`push_back`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/push_back.md) , [`operator+=`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator+=.md),
[`emplace_back`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/emplace_back.md), [`insert`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/insert.md), and [`operator[]`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator[].md) for a non-existing
index) can yield a reallocation, in which case all iterators (including the [`end()`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/end.md) iterator) and all
references to the elements are invalidated.

For [`ordered_json`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/ordered_json.md), also all operations that add a value to an **object**
([`push_back`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/push_back.md), [`operator+=`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator+=.md), [`emplace`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/emplace.md), [`insert`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/insert.md),
[`update`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/update.md), and [`operator[]`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator[].md) for a non-existing key) can yield a reallocation, in
which case all iterators (including the [`end()`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/end.md) iterator) and all references to the elements are invalidated.

## Requirements

The class satisfies the following concept requirements:

### Basic

- [DefaultConstructible](https://en.cppreference.com/w/cpp/named_req/DefaultConstructible): JSON values can be
  default-constructed. The result will be a JSON null value.
- [MoveConstructible](https://en.cppreference.com/w/cpp/named_req/MoveConstructible): A JSON value can be constructed
  from an rvalue argument.
- [CopyConstructible](https://en.cppreference.com/w/cpp/named_req/CopyConstructible): A JSON value can be
  copy-constructed from an lvalue expression.
- [MoveAssignable](https://en.cppreference.com/w/cpp/named_req/MoveAssignable): A JSON value can be assigned from an
  rvalue argument.
- [CopyAssignable](https://en.cppreference.com/w/cpp/named_req/CopyAssignable): A JSON value can be copy-assigned from
  an lvalue expression.
- [Destructible](https://en.cppreference.com/w/cpp/named_req/Destructible): JSON values can be destructed.

### Layout

- [StandardLayoutType](https://en.cppreference.com/w/cpp/named_req/StandardLayoutType): JSON values have
  [standard layout](https://en.cppreference.com/w/cpp/language/data_members#Standard_layout): All non-static data
  members are private and standard layout types, the class has no virtual functions or (virtual) base classes.

### Library-wide

- [EqualityComparable](https://en.cppreference.com/w/cpp/named_req/EqualityComparable): JSON values can be compared with
  `==`, see [`operator==`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator_eq.md).
- [LessThanComparable](https://en.cppreference.com/w/cpp/named_req/LessThanComparable): JSON values can be compared with
  `<`, see [`operator<`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator_le.md).
- [Swappable](https://en.cppreference.com/w/cpp/named_req/Swappable): Any JSON lvalue or rvalue of can be swapped with
  any lvalue or rvalue of other compatible types, using unqualified function `swap`.
- [NullablePointer](https://en.cppreference.com/w/cpp/named_req/NullablePointer): JSON values can be compared against
  `std::nullptr_t` objects which are used to model the `null` value.

### Container

- [Container](https://en.cppreference.com/w/cpp/named_req/Container): JSON values can be used like STL containers and
  provide iterator access.
- [ReversibleContainer](https://en.cppreference.com/w/cpp/named_req/ReversibleContainer): JSON values can be used like
  STL containers and provide reverse iterator access.

## Member types

- [**adl_serializer**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/adl_serializer/index.md) - the default serializer
- [**value_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/value_t.md) - the JSON type enumeration
- [**json_pointer**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/json_pointer/index.md) - JSON Pointer implementation
- [**json_serializer**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/json_serializer.md) - type of the serializer to for conversions from/to JSON
- [**error_handler_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/error_handler_t.md) - type to choose behavior on decoding errors
- [**cbor_tag_handler_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/cbor_tag_handler_t.md) - type to choose how to handle CBOR tags
- **initializer_list_t** - type for initializer lists of `basic_json` values
- [**input_format_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/input_format_t.md) - type to choose the format to parse
- [**json_sax_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/json_sax/index.md) - type for SAX events

### Exceptions

- [**exception**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/exception.md) - general exception of the `basic_json` class
    - [**parse_error**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/parse_error.md) - exception indicating a parse error
    - [**invalid_iterator**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/invalid_iterator.md) - exception indicating errors with iterators
    - [**type_error**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/type_error.md) - exception indicating executing a member function with a wrong type
    - [**out_of_range**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/out_of_range.md) - exception indicating access out of the defined range
    - [**other_error**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/other_error.md) - exception indicating other library errors

### Container types

| Type                     | Definition                                                                                                |
|--------------------------|-----------------------------------------------------------------------------------------------------------|
| `value_type`             | `#!cpp basic_json`                                                                                        |
| `reference`              | `#!cpp value_type&`                                                                                       |
| `const_reference`        | `#!cpp const value_type&`                                                                                 |
| `difference_type`        | `#!cpp std::ptrdiff_t`                                                                                    |
| `size_type`              | `#!cpp std::size_t`                                                                                       |
| `allocator_type`         | `#!cpp AllocatorType<basic_json>`                                                                         |
| `pointer`                | `#!cpp std::allocator_traits<allocator_type>::pointer`                                                    |
| `const_pointer`          | `#!cpp std::allocator_traits<allocator_type>::const_pointer`                                              |
| `iterator`               | [LegacyBidirectionalIterator](https://en.cppreference.com/w/cpp/named_req/BidirectionalIterator)          |
| `const_iterator`         | constant [LegacyBidirectionalIterator](https://en.cppreference.com/w/cpp/named_req/BidirectionalIterator) |
| `reverse_iterator`       | reverse iterator, derived from `iterator`                                                                 |
| `const_reverse_iterator` | reverse iterator, derived from `const_iterator`                                                           |
| `iteration_proxy`        | helper type for [`items`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/items.md) function                                                              |

### JSON value data types

- [**array_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/array_t.md) - type for arrays
- [**binary_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/binary_t.md) - type for binary arrays
- [**boolean_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/boolean_t.md) - type for booleans
- [**default_object_comparator_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/default_object_comparator_t.md) - default comparator for objects
- [**number_float_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/number_float_t.md) - type for numbers (floating-point)
- [**number_integer_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/number_integer_t.md) - type for numbers (integer)
- [**number_unsigned_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/number_unsigned_t.md) - type for numbers (unsigned)
- [**object_comparator_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/object_comparator_t.md) - comparator for objects
- [**object_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/object_t.md) - type for objects
- [**string_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/string_t.md) - type for strings

### Parser callback

- [**parse_event_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/parse_event_t.md) - parser event types
- [**parser_callback_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/parser_callback_t.md) - per-element parser callback type

## Member functions

- [(constructor)](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/basic_json.md)
- [(destructor)](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/~basic_json.md)
- [**operator=**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator=.md) - copy assignment
- [**array**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/array.md) (_static_) - explicitly create an array
- [**binary**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/binary.md) (_static_) - explicitly create a binary array
- [**object**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/object.md) (_static_) - explicitly create an object

### Object inspection

Functions to inspect the type of a JSON value.

- [**type**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/type.md) - return the type of the JSON value
- [**operator value_t**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator_value_t.md) - return the type of the JSON value
- [**type_name**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/type_name.md) - return the type as string
- [**is_primitive**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_primitive.md) - return whether the type is primitive
- [**is_structured**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_structured.md) - return whether the type is structured
- [**is_null**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_null.md) - return whether the value is null
- [**is_boolean**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_boolean.md) - return whether the value is a boolean
- [**is_number**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_number.md) - return whether the value is a number
- [**is_number_integer**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_number_integer.md) - return whether the value is an integer number
- [**is_number_unsigned**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_number_unsigned.md) - return whether the value is an unsigned integer number
- [**is_number_float**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_number_float.md) - return whether the value is a floating-point number
- [**is_object**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_object.md) - return whether the value is an object
- [**is_array**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_array.md) - return whether the value is an array
- [**is_string**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_string.md) - return whether the value is a string
- [**is_binary**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_binary.md) - return whether the value is a binary array
- [**is_discarded**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/is_discarded.md) - return whether the value is discarded

Optional functions to access the [diagnostic positions](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/macros/json_diagnostic_positions.md).

- [**start_pos**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/start_pos.md) - return the start position of the value
- [**end_pos**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/end_pos.md) - return the one past the end position of the value

### Value access

Direct access to the stored value of a JSON value.

- [**get**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/get.md) - get a value
- [**get_to**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/get_to.md) - get a value and write it to a destination
- [**get_ptr**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/get_ptr.md) - get a pointer value
- [**get_ref**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/get_ref.md) - get a reference value
- [**operator ValueType**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator_ValueType.md) - get a value
- [**get_binary**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/get_binary.md) - get a binary value

### Element access

Access to the JSON value

- [**at**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/at.md) - access specified element with bounds checking
- [**operator[]**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator[].md) - access specified element
- [**value**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/value.md) - access specified object element with default value
- [**front**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/front.md) - access the first element
- [**back**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/back.md) - access the last element

### Lookup

- [**find**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/find.md) - find an element in a JSON object
- [**count**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/count.md) - returns the number of occurrences of a key in a JSON object
- [**contains**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/contains.md) - check the existence of an element in a JSON object

### Iterators

- [**begin**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/begin.md) - returns an iterator to the first element
- [**cbegin**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/cbegin.md) - returns a const iterator to the first element
- [**end**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/end.md) - returns an iterator to one past the last element
- [**cend**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/cend.md) - returns a const iterator to one past the last element
- [**rbegin**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/rbegin.md) - returns an iterator to the reverse-beginning
- [**rend**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/rend.md) - returns an iterator to the reverse-end
- [**crbegin**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/crbegin.md) - returns a const iterator to the reverse-beginning
- [**crend**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/crend.md) - returns a const iterator to the reverse-end
- [**items**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/items.md) - wrapper to access iterator member functions in range-based for

### Capacity

- [**empty**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/empty.md) - checks whether the container is empty
- [**size**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/size.md) - returns the number of elements
- [**max_size**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/max_size.md) - returns the maximum possible number of elements

### Modifiers

- [**clear**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/clear.md) - clears the contents
- [**push_back**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/push_back.md) - add a value to an array/object
- [**operator+=**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator+=.md) - add a value to an array/object
- [**emplace_back**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/emplace_back.md) - add a value to an array
- [**emplace**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/emplace.md) - add a value to an object if a key does not exist
- [**erase**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/erase.md) - remove elements
- [**insert**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/insert.md) - inserts elements
- [**update**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/update.md) - updates a JSON object from another object, overwriting existing keys 
- [**swap**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/swap.md) - exchanges the values

### Lexicographical comparison operators

- [**operator==**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator_eq.md) - comparison: equal
- [**operator!=**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator_ne.md) - comparison: not equal
- [**operator<**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator_lt.md) - comparison: less than
- [**operator>**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator_gt.md) - comparison: greater than
- [**operator<=**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator_le.md) - comparison: less than or equal
- [**operator>=**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator_ge.md) - comparison: greater than or equal
- [**operator<=>**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/operator_spaceship.md) - comparison: 3-way

### Serialization / Dumping

- [**dump**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/dump.md) - serialization

### Deserialization / Parsing

- [**parse**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/parse.md) (_static_) - deserialize from a compatible input
- [**accept**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/accept.md) (_static_) - check if the input is valid JSON
- [**sax_parse**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/sax_parse.md) (_static_) - generate SAX events

### JSON Pointer functions

- [**flatten**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/flatten.md) - return flattened JSON value
- [**unflatten**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/unflatten.md) - unflatten a previously flattened JSON value

### JSON Patch functions

- [**patch**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/patch.md) - applies a JSON patch
- [**patch_inplace**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/patch_inplace.md) - applies a JSON patch in place
- [**diff**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/diff.md) (_static_) - creates a diff as a JSON patch

### JSON Merge Patch functions

- [**merge_patch**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/merge_patch.md) - applies a JSON Merge Patch

## Static functions

- [**meta**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/meta.md) - returns version information on the library
- [**get_allocator**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/get_allocator.md) - returns the allocator associated with the container

### Binary formats

- [**from_bjdata**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/from_bjdata.md) (_static_) - create a JSON value from an input in BJData format
- [**from_bson**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/from_bson.md) (_static_) - create a JSON value from an input in BSON format
- [**from_cbor**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/from_cbor.md) (_static_) - create a JSON value from an input in CBOR format
- [**from_msgpack**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/from_msgpack.md) (_static_) - create a JSON value from an input in MessagePack format
- [**from_ubjson**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/from_ubjson.md) (_static_) - create a JSON value from an input in UBJSON format
- [**to_bjdata**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/to_bjdata.md) (_static_) - create a BJData serialization of a given JSON value
- [**to_bson**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/to_bson.md) (_static_) - create a BSON serialization of a given JSON value
- [**to_cbor**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/to_cbor.md) (_static_) - create a CBOR serialization of a given JSON value
- [**to_msgpack**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/to_msgpack.md) (_static_) - create a MessagePack serialization of a given JSON value
- [**to_ubjson**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/to_ubjson.md) (_static_) - create a UBJSON serialization of a given JSON value

## Non-member functions

- [**operator<<(std::ostream&)**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/operator_ltlt.md) - serialize to stream
- [**operator>>(std::istream&)**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/operator_gtgt.md) - deserialize from stream
- [**to_string**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/to_string.md) - user-defined `to_string` function for JSON values

## Literals

- [**operator""_json**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/operator_literal_json.md) - user-defined string literal for JSON values

## Helper classes

- [**std::hash&lt;basic_json&gt;**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/std_hash.md) - return a hash value for a JSON object
- [**std::swap&lt;basic_json&gt;**](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/std_swap.md) - exchanges the values of two JSON objects

## Examples

??? example

    The example shows how the library is used.
    
    ```cpp
    --8<-- "examples/README.cpp"
    ```
    
    Output:
    
    ```json
    --8<-- "examples/README.output"
    ```

## See also

- [RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format](https://tools.ietf.org/html/rfc8259)

## Version history

- Added in version 1.0.0.
