---
description: Read, write, and visualize MCAP files containing JSON data.
---

# JSON

## Read and write MCAP

If you're starting from scratch, you can write code that allows you to **write your JSON data to MCAP files** and subsequently **read your JSON data from your MCAP files**.

### Guides

- [Python](01-doing/00-华威科实习/01-项目工作台/05-参考资料/ROS-git-worktree/src/VTLA_octopus-master/octopus/3rdparty/mcap/website/docs/guides/python/json.md)

### Examples

- [Python](https://github.com/foxglove/mcap/tree/main/python/examples/jsonschema) - [CSV to MCAP converter](https://github.com/foxglove/mcap/blob/main/python/examples/jsonschema/pointcloud_csv_to_mcap.py)
- [C++](https://github.com/foxglove/mcap/tree/main/cpp/examples/jsonschema) - [reader](https://github.com/foxglove/mcap/tree/main/cpp/examples/jsonschema/reader.cpp), [writer](https://github.com/foxglove/mcap/tree/main/cpp/examples/jsonschema/writer.cpp)

## Inspect MCAP

Use the [`mcap` CLI tool](https://github.com/foxglove/mcap/tree/main/go/cli/mcap) to inspect MCAP files, validate their contents, and even echo their messages to `stdout`.

For an exhaustive list of ways to interact with your MCAP data, check out the [`mcap` GitHub repo](https://github.com/foxglove/mcap/tree/main/go/cli/mcap).

## Visualize MCAP

[Foxglove](https://foxglove.dev/) supports playing back local and remote MCAP files containing JSON data.
