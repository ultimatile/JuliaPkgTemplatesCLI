# JuliaPkgTemplatesCLI

> [!WARNING]
> This is a beta version of JuliaPkgTemplatesCLI. The software is in active development and may contain bugs or breaking changes. Use at your own risk and expect frequent updates.

## Overview

JuliaPkgTemplatesCLI (`jtc`) is a command-line tool for generating Julia packages using [PkgTemplates.jl](https://github.com/JuliaCI/PkgTemplates.jl) with integrated [mise](https://github.com/jdx/mise) task management. It streamlines the Julia package creation process by:

- Generating Julia packages using PkgTemplates.jl templates with comprehensive plugin support
- Integrating with mise tasks for Pkg.jl related commands (e.g., `add`, `rm`, `instantiate`, etc.) to manage dependencies
- Providing configurable settings with user defaults and plugin-specific options
- Supporting shell completion (currently fish shell) for improved developer experience

## Quick start without installation

You can try JuliaPkgTemplatesCLI without installing it using `uvx`:

```bash
# Create a simple Julia package
uvx --from git+https://github.com/ultimatile/JuliaPkgTemplatesCLI jtc create MyPackage.jl
```

## Installation

### From GitHub Repository

You can install directly from the GitHub repository:

```bash
# Install from the latest commit on main branch
uv tool install git+https://github.com/ultimatile/JuliaPkgTemplatesCLI.git

# Install from a specific release tag
uv tool install git+https://github.com/ultimatile/JuliaPkgTemplatesCLI.git@v0.3.0
```

### From Source

For development or testing the latest changes:

```bash
git clone https://github.com/ultimatile/JuliaPkgTemplatesCLI.git
cd JuliaPkgTemplatesCLI
uv tool install .
```

## Prerequisites

- Python 3.11 or higher
- Julia 1.6 or higher
- [PkgTemplates.jl](https://github.com/JuliaCI/PkgTemplates.jl) installed in Julia. Currently This package is based on PkgTemplates.jl v0.7.56 but doesn’t lock its version, so it may break if users install a newer PkgTemplates.jl release.
- [mise](https://github.com/jdx/mise) (optional, for mise task integration)

### Runtime Dependencies

- Click (command-line interface)
- Jinja2 (template rendering)

### Development Dependencies

- uv (package management)
- pytest (testing)
- pyright (type checking)
- ruff (code linting)

## Shell Completion

To enable shell completion for `jtc`, you can use the following command (`.config` directory can be changed based on your environment):

For fish:

```bash
echo 'jtc completion | source' > ~/.config/fish/completions/jtc.fish
```

Currently, shell completion is only available for fish shell.

## Usage

JuliaPkgTemplatesCLI provides four main commands:

- `jtc create <package_name>`: Generate a new Julia package using PkgTemplates.jl
- `jtc config`: Manage configuration settings with `show` and `set` subcommands
- `jtc plugin-info [plugin_name]`: Display information about available plugins
- `jtc completion`: Generate shell completion scripts

### Basic Usage Examples

```bash
# Show help
jtc --help

# Create a new Julia package with minimal options
jtc create MyPackage.jl

# Create a package with specific author and output directory
jtc create MyPackage.jl --user "Your Name" --output-dir ~/projects

# Create a package with specific license and plugins
jtc create MyPackage.jl --license Apache --formatter style=sciml

# Create a package with plugin-specific options
jtc create MyPackage.jl --git ssh=true

# Create a package with custom mise filename
jtc create MyPackage.jl --mise-filename-base "mise"

# Create a package without mise integration
jtc create MyPackage.jl --no-mise

# Dry run to see what would be executed
jtc create MyPackage.jl --dry-run

# Show current version
jtc --version
```

### Configuration Management

````bash
# Show current configuration
jtc config # or jtc config show

# Set configuration values
jtc config --user "Your Name" --license MIT --formatter style=sciml

# Set plugin-specific defaults
jtc config --formatter style=blue
```

### Plugin Information

```bash
# List all available plugins
jtc plugin-info

# Show details for a specific plugin
jtc plugin-info Formatter
````

## Configuration

jtc supports user-configurable defaults to streamline package creation. Configuration is stored in `~/$XDG_CONFIG_HOME/jtc/config.toml` (default is `~/.config/jtc/config.toml`) following XDG Base Directory standards.

### Configuration File Format

The configuration file uses TOML format:

```toml
[default]
author = "Your Name"
user = "github_username"
mail = "your.email@example.com"
license = "MIT"
mise_filename_base = ".mise"
with_mise = true

[default.formatter]
style = "blue"
```

### Configuration Precedence

1. **Command-line options** (highest priority)
2. **Configuration file defaults**
3. **Built-in defaults** (lowest priority)

For example, if you have `author = "Config Author"` in your config file but run `jtc create MyPackage --author "CLI Author"`, the CLI argument takes precedence.

### Available Options

#### Core Options

- **author**: Default author name for packages
- **user**: Git hosting username for repository URLs and CI
- **mail**: Email address for package metadata
- **license**: Default license type (`MIT`, `Apache`, `BSD2`, `BSD3`, `GPL2`, `GPL3`, `MPL`, `ISC`, `LGPL2`, `LGPL3`, `AGPL3`, `EUPL`)
- **mise-filename-base**: Base name for mise config file (e.g., `.mise` creates `.mise.toml`, `mise` creates `mise.toml`)
- **with-mise**: Enable/disable mise task file generation (default: enabled)

#### Plugin Options

All [PkgTemplates.jl](https://github.com/JuliaCI/PkgTemplates.jl) plugins are supported with their respective options:

- **CompatHelper**: Automated dependency updates
- **TagBot**: Automated GitHub releases
- **Documenter**: Documentation generation and deployment
- **Codecov**: Code coverage reporting
- **GitHubActions**: CI/CD workflows
- **ProjectFile**: Package metadata management
- **Formatter**: Code formatting with JuliaFormatter
- **Tests**: Testing framework setup
- **Git**: Git repository initialization

Use `jtc plugin-info [plugin_name]` to see available options for each plugin.

### Configuration Location

Configuration files are stored in `~/.config/jtc/config.toml` following XDG Base Directory standards.

If `XDG_CONFIG_HOME` environment variable is set, that location will be used instead.

## Development

For development setup:

```bash
git clone https://github.com/ultimatile/JuliaPkgTemplatesCLI.git
cd JuliaPkgTemplatesCLI
uv sync
```

### Development Commands

```bash
# Run the CLI tool
uv run jtc --help

# Run tests (all)
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test
uv run pytest tests/test_cli.py::TestCreateCommand::test_create_with_valid_package_name -v

# Type checking with pyright
uv run pyright

# Linting with ruff
uv run ruff check

# Install from source for testing
uv tool install .
```

## Release

The project uses semantic versioning with automated GitHub releases.
For detailed CI/CD workflow information, see [`docs/workflow.md`](docs/workflow.md).

**For maintainers**: Create PR with title containing "release".
GitHub Actions will automatically update the title to "release: v{version}" and handle the release process.

## Related Projects

- [jlpkg](https://github.com/fredrikekre/jlpkg): Pkg.jl-related CLI. If you use jlpkg, you may not need mise tasks integration in jtc.
