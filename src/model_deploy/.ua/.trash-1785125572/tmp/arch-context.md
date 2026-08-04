# Architecture Context Files

## Language: python
# Python Language Prompt Snippet

## Key Concepts

- **Decorators**: Functions that wrap other functions or classes using `@decorator` syntax
- **List/Dict Comprehensions**: Concise syntax for creating collections from iterables
- **Generators and Yield**: Lazy iterators using `yield` for memory-efficient data processing
- **Context Managers**: `with` statement for resource management via `__enter__`/`__exit__`
- **Type Hints and Typing Module**: Optional static type annotations for tooling and documentation
- **Dunder Methods**: Special methods like `__init__`, `__repr__`, `__eq__` defining object behavior
- **Metaclasses**: Classes that define how other classes are created (type as default metaclass)
- **Dataclasses**: `@dataclass` decorator auto-generating boilerplate from field annotations
- **Protocols**: Structural subtyping via `typing.Protocol` for duck-type-safe interfaces
- **Descriptors**: Objects defining `__get__`, `__set__`, `__delete__` to customize attribute access
- **Async/Await with Asyncio**: Cooperative concurrency using coroutines and an event loop

## Import Patterns

- `from module import name` — import specific name from module
- `import module` — import entire module, access via `module.name`
- `from package.module import name` — absolute import from nested package
- `from . import relative` — relative import within a package

## File Patterns

- `__init__.py` — package initializer (barrel equivalent), can re-export public API
- `__main__.py` — package entry point when run with `python -m package`
- `conftest.py` — pytest shared fixtures and hooks (auto-discovered)
- `setup.py` / `pyproject.toml` — project configuration and build metadata
- `requirements.txt` — pinned dependency list

## Common Frameworks

- **Django** — Full-stack web framework with ORM, admin, and batteries included
- **FastAPI** — Modern async API framework with automatic OpenAPI docs
- **Flask** — Lightweight WSGI micro-framework for web applications
- **SQLAlchemy** — SQL toolkit and ORM with unit-of-work pattern
- **Celery** — Distributed task queue for background job processing
- **Pydantic** — Data validation and settings management using type annotations

## Example Language Notes

> Uses `@dataclass` decorator to auto-generate `__init__`, `__repr__`, and `__eq__` from
> field annotations. This eliminates boilerplate while keeping the class definition
> readable and the generated methods consistent.
>
> When `__init__.py` re-exports symbols, it acts as the package's public API surface —
> consumers import from the package rather than reaching into internal modules.

## Language: cpp
# C++ Language Prompt Snippet

## Key Concepts

- **Templates**: Function, class, and variadic templates for generic compile-time polymorphism
- **RAII**: Resource Acquisition Is Initialization — tie resource lifetime to object scope
- **Smart Pointers**: `unique_ptr` (exclusive), `shared_ptr` (reference-counted), `weak_ptr` (non-owning)
- **Move Semantics**: Rvalue references (`&&`) and `std::move` for efficient resource transfer
- **Operator Overloading**: Define custom behavior for operators on user-defined types
- **Virtual Functions and Vtable**: Runtime polymorphism through virtual method dispatch tables
- **Namespaces**: Organize symbols and prevent name collisions across translation units
- **Constexpr**: Compile-time evaluation of functions and variables for zero-runtime-cost computation
- **Lambda Expressions**: Anonymous functions with capture lists for closures
- **STL Containers and Algorithms**: Standard containers (vector, map, set) and generic algorithms
- **Concepts (C++20)**: Named constraints on template parameters replacing SFINAE patterns

## Import Patterns

- `#include <system_header>` — include standard library or system headers
- `#include "local_header.h"` — include project-local header files
- `using namespace std` — bring all names from std into scope (avoid in headers)
- `using std::vector` — selectively bring specific names into scope

## File Patterns

- `.h` / `.hpp` — header files containing declarations, templates, and inline definitions
- `.cpp` / `.cc` — implementation files with function definitions and static data
- `CMakeLists.txt` — CMake build system configuration
- `Makefile` — Make-based build rules and targets
- `main.cpp` — program entry point containing `int main()`

## Common Frameworks

- **Qt** — Cross-platform application framework with signal/slot mechanism
- **Boost** — Extensive collection of peer-reviewed portable libraries
- **Catch2** — Header-only testing framework with BDD-style syntax
- **Google Test** — Testing framework with fixtures, assertions, and mocking
- **gRPC** — High-performance RPC framework for service communication

## Example Language Notes

> Uses `std::unique_ptr<T>` for RAII-based ownership, ensuring deterministic cleanup
> when scope exits. The unique pointer cannot be copied, only moved, making ownership
> transfer explicit and preventing accidental double-free errors.
>
> Header/implementation separation (`.h`/`.cpp`) controls compilation boundaries —
> changes to a `.cpp` file only recompile that translation unit, not all includers.

## Language: yaml
# YAML Language Prompt Snippet

## Key Concepts

- **Indentation-Based Nesting**: Whitespace-sensitive structure (spaces only, no tabs) defining hierarchy
- **Anchors and Aliases**: `&anchor` defines a reusable block, `*anchor` references it to avoid duplication
- **Merge Keys**: `<<: *anchor` merges anchor contents into the current mapping
- **Multi-Line Strings**: Literal block (`|`) preserves newlines, folded block (`>`) joins lines
- **Document Separators**: `---` starts a new document, `...` ends one (multi-document streams)
- **Tags and Types**: `!!str`, `!!int`, `!!bool` for explicit typing; custom tags for application-specific types
- **Flow Style**: Inline JSON-like syntax `{key: value}` and `[item1, item2]` for compact notation
- **Environment Variable Substitution**: `${VAR}` patterns used in docker-compose and CI configs

## Notable File Patterns

- `docker-compose.yml` / `docker-compose.yaml` — Multi-container Docker application definition
- `.github/workflows/*.yml` — GitHub Actions CI/CD workflow definitions
- `.gitlab-ci.yml` — GitLab CI/CD pipeline configuration
- `kubernetes/*.yaml` / `k8s/*.yaml` — Kubernetes resource manifests
- `*.config.yaml` — Application configuration files
- `mkdocs.yml` — MkDocs documentation site configuration
- `serverless.yml` — Serverless Framework configuration

## Edge Patterns

- YAML config files `configures` the code modules they control (e.g., database settings affect data layer)
- CI/CD YAML files `triggers` build and deployment pipelines
- docker-compose YAML `deploys` services and `depends_on` Dockerfiles
- Kubernetes YAML `deploys` and `provisions` application services

## Summary Style

> "Docker Compose configuration defining N services with networking, volumes, and health checks."
> "GitHub Actions workflow running tests on push and deploying to production on merge to main."
> "Kubernetes deployment manifest with N replicas, resource limits, and liveness probes."

## Language: markdown
# Markdown Language Prompt Snippet

## Key Concepts

- **Heading Hierarchy**: `#` through `######` for document structure, with h1 as the title
- **Front Matter**: YAML metadata between `---` delimiters at the top of the file
- **Fenced Code Blocks**: Triple backticks with optional language identifier for syntax highlighting
- **Reference-Style Links**: `[text][ref]` with `[ref]: url` definitions, useful for repeated URLs
- **Tables**: Pipe-delimited columns with alignment markers (`:---`, `:---:`, `---:`)
- **Admonitions**: Blockquote-based callouts (`> **Note:**`, `> **Warning:**`) for emphasis
- **Task Lists**: `- [ ]` and `- [x]` for checklists in issue trackers and READMEs
- **HTML Embedding**: Raw HTML allowed inline for features Markdown does not support natively

## Notable File Patterns

- `README.md` — Project overview and entry point for new contributors (high-value)
- `CONTRIBUTING.md` — Contribution guidelines, code style, PR process
- `CHANGELOG.md` — Version history following Keep a Changelog or similar format
- `docs/**/*.md` — Documentation directory with guides, API references, tutorials
- `*.md` in source directories — Co-located documentation for modules or packages
- `ADR-*.md` or `adr/*.md` — Architecture Decision Records

## Edge Patterns

- Markdown files `documents` the code components they describe or reference
- Links to other `.md` files create `related` edges between documentation nodes
- Code block references mentioning file paths may imply `documents` edges to those files
- README files in subdirectories typically `documents` the module at that path

## Summary Style

> "Project overview documentation with N sections covering installation, usage, and API reference."
> "Architecture Decision Record documenting the choice of [technology] for [purpose]."
> "Contributing guide with code style rules, testing requirements, and pull request process."

## Language: shell
# Shell Language Prompt Snippet

## Key Concepts

- **Shebang Line**: `#!/bin/bash` or `#!/usr/bin/env bash` specifying the interpreter
- **Variables**: `VAR=value` assignment, `$VAR` or `${VAR}` expansion, no spaces around `=`
- **Functions**: `function name()` or `name()` for reusable command groups
- **Conditionals**: `if [[ condition ]]; then ... fi` with `[[ ]]` for extended tests
- **Loops**: `for item in list`, `while condition`, `until condition` iteration patterns
- **Pipes and Redirection**: `|` for chaining commands, `>` / `>>` / `2>&1` for output redirection
- **Exit Codes**: `$?` captures last command status; `set -e` exits on any failure
- **Strict Mode**: `set -euo pipefail` for robust error handling (exit on error, undefined vars, pipe failures)
- **Command Substitution**: `$(command)` captures command output as a string
- **Here Documents**: `<<EOF ... EOF` for multi-line string input to commands

## Notable File Patterns

- `*.sh` / `*.bash` — Shell script files
- `scripts/*.sh` — Project automation scripts (build, deploy, setup)
- `entrypoint.sh` — Docker container entry point script
- `install.sh` / `setup.sh` — Environment setup scripts
- `.bashrc` / `.bash_profile` / `.zshrc` — Shell configuration files

## Edge Patterns

- Shell scripts `triggers` other scripts or build processes they invoke
- Entry point scripts `deploys` the application they start
- Setup scripts `configures` the development environment
- Build scripts `depends_on` the source files they compile or package

## Summary Style

> "Build automation script compiling TypeScript, running tests, and packaging the release artifact."
> "Docker entry point script handling signal forwarding and graceful shutdown."
> "Environment setup script installing dependencies and configuring development tools."

## Language: json
# JSON Language Prompt Snippet

## Key Concepts

- **Strict Syntax**: No trailing commas, no comments (unlike JSONC or JSON5), double-quoted strings only
- **Data Types**: Objects, arrays, strings, numbers, booleans, and null — no undefined or date types
- **Nested Structure**: Arbitrary nesting depth for hierarchical configuration or data
- **Schema Validation**: JSON Schema (`$schema` keyword) for validating structure and types
- **JSONC**: JSON with Comments variant used by VS Code, tsconfig.json, and other tooling
- **JSON5**: Extended JSON allowing comments, trailing commas, unquoted keys, and more
- **JSON Lines** (`.jsonl`): One JSON object per line for streaming data processing

## Notable File Patterns

- `package.json` — Node.js project manifest with dependencies, scripts, and metadata
- `tsconfig.json` — TypeScript compiler configuration (actually JSONC)
- `.eslintrc.json` — ESLint linting rules and configuration
- `*.schema.json` — JSON Schema definitions for validation
- `composer.json` — PHP Composer project manifest
- `appsettings.json` — .NET application configuration
- `manifest.json` — Browser extension or PWA manifest

## Edge Patterns

- `package.json` `configures` the build toolchain and defines project dependencies
- `tsconfig.json` `configures` TypeScript compilation for all `.ts` files
- JSON Schema files `defines_schema` for API request/response validation
- Config JSON files `configures` the runtime behavior of the application

## Summary Style

> "Node.js project manifest defining N dependencies, build scripts, and project metadata."
> "TypeScript compiler configuration enabling strict mode with path aliases for monorepo packages."
> "JSON Schema defining the request/response structure for the user API endpoint."

## Output Language Guidelines (zh)
# 中文输出指南 (Chinese Simplified)

本文件提供生成中文知识图谱内容的语言指导。

## 标签约定

推荐使用中文标签或英文通用技术术语：

| 模式 | 推荐标签 |
|------|---------|
| 入口文件 | `入口点`, `barrel`, `导出` 或 `entry-point` |
| 工具函数 | `工具函数`, `helpers`, `common` 或 `utility` |
| API处理器 | `api-handler`, `控制器`, `端点` |
| 数据模型 | `数据模型`, `entity`, `schema` 或 `data-model` |
| 测试文件 | `测试`, `单元测试`, `test` |
| 配置文件 | `配置`, `构建系统`, `settings` 或 `configuration` |
| 基础设施 | `基础设施`, `部署`, `容器化` 或 `infrastructure` |
| 文档 | `文档`, `指南`, `参考` 或 `documentation` |

**混合策略：** 通用技术术语保留英文（如 `middleware`, `api-handler`），描述性标签可使用中文。

## 摘要风格

用中文撰写1-2句摘要：
- 描述文件的**目的**和**作用**
- 使用主动语态（"提供...", "处理...", "管理..."）
- 避免重复文件名

**示例：**
- 好: "提供日期格式化和字符串清洗工具函数，被 API 层广泛使用。"
- 差: "utils 文件包含工具函数。"

## 技术术语

以下术语建议保留英文（暂无标准翻译）：
- `middleware`, `hook`, `barrel`, `entry-point`
- `ORM`, `REST API`, `CI/CD`, `CRUD`
- `singleton`, `factory`, `observer`
- `interceptor`, `guard`

## 层级名称

使用中文层级名称：
- `API 层`, `服务层`, `数据层`, `UI 层`
- `基础设施`, `配置`, `文档`
- `工具层`, `中间件层`, `测试层`

或保留英文（根据团队习惯）：
- `API Layer`, `Service Layer`, `Data Layer`