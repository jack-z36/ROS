# Trailing Commas

Like [comments](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/features/comments.md), this library does not support trailing commas in arrays and objects *by default*.

You can set parameter `ignore_trailing_commas` to `#!cpp true` in the [`parse`](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/json/docs/mkdocs/docs/api/basic_json/parse.md) function to allow trailing commas in arrays and objects. Note that a single comma as the only content of the array or object (`[,]` or `{,}`) is not allowed, and multiple trailing commas (`[1,,]`) are not allowed either.

This library does not add trailing commas when serializing JSON data.

For more information, see [JSON With Commas and Comments (JWCC)](https://nigeltao.github.io/blog/2021/json-with-commas-comments.html).

!!! example

    Consider the following JSON with trailing commas.

    ```json
    {
        "planets": [
            "Mercury",
            "Venus",
            "Earth",
            "Mars",
            "Jupiter",
            "Uranus",
            "Neptune",
        ]
    }
    ```
    
    When calling `parse` without additional argument, a parse error exception is thrown. If `ignore_trailing_commas` is set to `#! true`, the trailing commas are ignored during parsing:

    ```cpp
    --8<-- "examples/trailing_commas.cpp"
    ```

    Output:
    
    ```
    --8<-- "examples/trailing_commas.output"
    ```
