# JuliaPkgTemplatesCLI

> [!WARNING]
> This is a beta version of JuliaPkgTemplatesCLI. The software is in active development and may contain bugs or breaking changes. Use at your own risk and expect frequent updates.

## Overview

JuliaPkgTemplatesCLI (`jtc`) is a command-line tool for generating Julia packages using [PkgTemplates.jl](https://github.com/JuliaCI/PkgTemplates.jl) with integrated [mise](https://github.com/jdx/mise) task management. It streamlines the Julia package creation process by:

- **Integrated mise task management**: Automatically generates mise tasks for common Pkg.jl operations (`add`, `rm`, `instantiate`, etc.)
- **Flexible configuration**: User-configurable defaults with plugin-specific options via CLI or config files

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
```

### From Source

For development or testing the latest changes:

```bash
git clone https://github.com/ultimatile/JuliaPkgTemplatesCLI.git
cd JuliaPkgTemplatesCLI
uv tool install .
```

## Prerequisites

- Python 3.10 or higher
- Julia 1.0 or higher
- [PkgTemplates.jl](https://github.com/JuliaCI/PkgTemplates.jl) installed in Julia. Currently This package is based on PkgTemplates.jl v0.7.56 but doesn’t lock its version, so it may break if users install a newer PkgTemplates.jl release.
- [mise](https://github.com/jdx/mise) (optional, for mise task integration)

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

# Create a package with multiple authors
jtc create MyPackage.jl --author "Author One" --author "Author Two <author2@example.com>"
# Or using comma-separated format
jtc create MyPackage.jl --author "Author One, Author Two"

# Create a package with specific license and plugins
jtc create MyPackage.jl --license Apache --formatter style=sciml --git ssh=true

# Create a package with default license (enables License plugin without arguments)
jtc create MyPackage.jl --license

# Create a package without mise integration
jtc create MyPackage.jl --no-mise

# Dry run to see what would be executed
jtc create MyPackage.jl --dry-run

# Show current version
jtc --version
```

### Configuration Management

```bash
# Show current configuration
jtc config # or jtc config show

# Set configuration values
jtc config --user "Your Name" --license MIT --formatter style=sciml

# Set plugin-specific defaults
jtc config --formatter style=blue

# Use an alternate configuration file
jtc config --config-file ~/.config/jtc/custom.toml --show
```

### Plugin Information

```bash
# List all available plugins
jtc plugin-info

# Show details for a specific plugin
jtc plugin-info Formatter
```

## Configuration

jtc supports user-configurable defaults to streamline package creation.
Configuration is stored in `~/$XDG_CONFIG_HOME/jtc/config.toml` (default is `~/.config/jtc/config.toml`) following XDG Base Directory standards.

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
- **mise-filename-base**: Base name for mise config file (e.g., `.mise` creates `.mise.toml`, `mise` creates `mise.toml`)
- **with-mise**: Enable/disable mise task file generation (default: enabled)

#### Plugin Support

JuliaPkgTemplatesCLI supports all plugins available in PkgTemplates.jl v0.7.56.
Plugin's options are passed as is, but License's name option is aliased to `license` in jtc config.
license: Default license type (supports all PkgTemplates.jl license identifiers plus aliases: `Apache`, `GPL2`, `GPL3`, `LGPL2`, `LGPL3`, `AGPL3`, `EUPL`)

#### Plugin Information and Options

Use the `jtc plugin-info` command to explore available plugins and their configuration options:

```bash
# List all available plugins with brief descriptions
jtc plugin-info

# Show detailed information and options for a specific plugin
jtc plugin-info Formatter
```

Each plugin supports various configuration options that can be set via:

- Command line: `jtc create MyPkg --formatter style=blue --git ssh=true`
- Configuration file: Set default options in `~/.config/jtc/config.toml`

#### Argument-less Plugins

Some plugins can be enabled without any arguments using a simple flag:

```bash
# Enable SrcDir plugin
jtc create MyPackage.jl --srcdir

# Enable multiple argument-less plugins
jtc create MyPackage.jl --srcdir --readme --citation

# Set in configuration
jtc config set --srcdir --gitlabci
```

Supported argument-less plugins: `SrcDir`, `GitLabCI`, `TravisCI`, `AppVeyor`, `CirrusCI`, `DroneCI`, `Readme`, `BlueStyleBadge`, `ColPracBadge`, `PkgEvalBadge`, `Citation`, `CodeOwners`, `Develop`

#### Plugin Option Merging with "+="

Use the `+=` operator to merge plugin options with existing configuration values instead of overriding them:

```bash
# Add to existing gitignore patterns (merges with config defaults)
jtc create MyPackage.jl --git ignore+=["custom_file","*.tmp"]

# Merge formatter options with config defaults
jtc config set --formatter style=blue

# Set boolean option (no += needed for boolean types)
jtc config set --git manifest=true
```

The `+=` operator behavior:
- **Arrays/Lists**: Appends new values to existing ones
- **Strings**: Concatenates with existing value
- **Other types**: Uses the new value if compatible with existing type

Without `+=`, the option value completely replaces the existing configuration.

### Configuration Location

Configuration files are stored in `~/.config/jtc/config.toml` following XDG Base Directory standards.

Use `--config-file` to read from or write to an alternative location, for example `jtc config set --config-file config.toml --author "Alt Author"`.

If `XDG_CONFIG_HOME` environment variable is set, that location will be used instead.

## Development

For development setup:

```bash
git clone https://github.com/ultimatile/JuliaPkgTemplatesCLI.git
cd JuliaPkgTemplatesCLI
uv sync
```

### Runtime Dependencies

- Click (command-line interface)
- Jinja2 (template rendering)

### Development Dependencies

- uv (package management)
- pytest (testing)
- pyright (type checking)
- ruff (code linting)
- make (build automation)
- python-semantic-release (automated versioning)
- GitHub CLI (`gh`) (optional, for automated release creation)

### Development Commands

```bash
# Run the CLI tool
uv run jtc --help

# Install from source for testing
uv tool install .
```

#### Testing and Quality Assurance

```bash
# Run tests
make test                    # or make t

# Run type checking
make typecheck              # or make c

# Run linting and formatting
make lint                   # or make l

# Run all checks (test + typecheck + lint)
make check                  # or make tcl

# Run specific test
uv run pytest tests/test_cli.py::TestCreateCommand::test_create_with_valid_package_name -v

# Clean build artifacts
make clean-artifacts
```

#### Release Management

```bash
# Show available commands
make help

# Complete release workflow (automated)
make release-full

# Manual release steps:
make release                # Prepare release (version bump, commit, tag, push)
make publish                # Create GitHub release
make restore-branch         # Return to original branch

# Debug version information
make debug-vars
```

## Related Projects

- [jlpkg](https://github.com/fredrikekre/jlpkg): Pkg.jl-related CLI. If you use jlpkg, you may not need mise tasks integration in jtc.
