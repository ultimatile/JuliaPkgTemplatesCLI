# JuliaPkgTemplatesCLI

> [!WARNING]
> This is a beta version of JuliaPkgTemplatesCLI. The software is in active development and may contain bugs or breaking changes. Use at your own risk and expect frequent updates.

## Overview

JuliaPkgTemplatesCLI (`jtc`) is a command-line tool for generating Julia packages using PkgTemplates.jl with integrated mise task management. It streamlines the Julia package creation process by:

- Generating Julia packages using PkgTemplates.jl templates with comprehensive plugin support
- Integrating with mise tasks for Pkg.jl related commands (e.g., `add`, `rm`, `instantiate`, etc.) to manage dependencies
- Providing configurable templates and settings with user defaults and plugin-specific options
- Supporting shell completion (currently fish shell) for improved developer experience

## Installation

### From GitHub Repository

Alternatively, you can install directly from the GitHub repository:

```bash
# Install from the latest commit on main branch
uv tool install git+https://github.com/ultimatile/JuliaPkgTemplatesCLI.git

# Install from a specific release tag
uv tool install git+https://github.com/ultimatile/JuliaPkgTemplatesCLI.git@v0.2.0
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
- PkgTemplates.jl installed in Julia
- mise (optional, for mise task integration)

### Runtime Dependencies

- Click (command-line interface)
- Jinja2 (template rendering)

### Development Dependencies

- pytest (testing)
- pyright (type checking)

## Shell Completion

To enable shell completion for `jtc`, you can use the following command (`.config` directory can be changed based on your environment):

For fish:

```bash
echo 'jtc completion | source' > ~/.config/fish/completions/jtc.fish
```

Currently, shell completion is only available for fish shell. Support for other shells (bash, zsh) will be added in future releases.

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
jtc create MyPackage

# Create a package with specific author and output directory
jtc create MyPackage --author "Your Name" --output-dir ~/projects

# Create a package with specific template and license
jtc create MyPackage --template full --license Apache

# Create a package with plugin-specific options
jtc create MyPackage --formatter "style=blue margin=92" --documenter "logo=assets/logo.png"

# Dry run to see what would be executed
jtc create MyPackage --dry-run

# Show current version
jtc --version
```

### Configuration Management

```bash
# Show current configuration
jtc config show # or jtc config

# Set configuration values (set subcommand can be omitted)
jtc config set --author "Your Name" --license MIT --template standard

# Set plugin-specific defaults
jtc config set --formatter "style=blue" --documenter "logo=assets/logo.png"
```

### Plugin Information

```bash
# List all available plugins
jtc plugin-info

# Show details for a specific plugin
jtc plugin-info Formatter
```

## Configuration

jtc supports user-configurable defaults to streamline package creation. Configuration is stored in `~/$XDG_CONFIG_HOME/jtc/config.toml` (default is `~/.config/jtc/config.toml`) following XDG Base Directory standards.

### Setting Defaults

```bash
# Set default author name
jtc config set --author "Your Name"

# Set default license
jtc config set --license Apache

# Set default template type
jtc config set --template full

# Set plugin-specific defaults
jtc config set --formatter "style=blue margin=92"

# Set multiple defaults at once
jtc config set --author "Your Name" --license MIT --template standard --formatter "style=sciml"

# View current configuration
jtc config show
```

### Configuration File Format

The configuration file uses TOML format:

```toml
[default]
author = "Your Name"
user = "github_username"
mail = "your.email@example.com"
license = "MIT"
template = "standard"

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
- **template**: Default template type (`minimal`, `standard`, `full`)

#### Plugin Options

All PkgTemplates.jl plugins are supported with their respective options:

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

## Beta Release Notes

- This beta version includes comprehensive plugin support and enhanced configuration management
- All major PkgTemplates.jl plugins are supported with full configuration options
- Shell completion is available for fish shell
- Enhanced CLI with subcommands for better user experience
- Configuration system supports both core settings and plugin-specific options
- Please report issues on the GitHub repository

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

# Install from source for testing
uv tool install .
```

## Release

The project uses semantic versioning with automated GitHub releases. For detailed CI/CD workflow information, see [`docs/workflow.md`](docs/workflow.md).

**For maintainers**: Create PR with title containing "release". GitHub Actions will automatically update the title to "release: v{version}" and handle the release process.
