# JuliaPkgTemplatesCLI

> [!WARNING]
> This is an alpha version of JuliaPkgTemplatesCLI. The software is in early development and may contain bugs, incomplete features, or breaking changes. Use at your own risk and expect frequent updates.

## Overview

JuliaPkgTemplatesCLI (`jtc`) is a command-line tool for generating Julia packages using PkgTemplates.jl with integrated mise task management. It streamlines the Julia package creation process by:

- Generating Julia packages using PkgTemplates.jl templates.
- Integrating with mise tasks for Pkg.jl related commands (e.g., `add`, `rm`, `instantiate`, etc.) to manage dependencies.
- Providing configurable templates and settings with user defaults. See [Configuration](#configuration) for details.

## Installation

### From GitHub Repository

Alternatively, you can install directly from the GitHub repository:

```bash
# Install from the latest commit on main branch
uv tool install git+https://github.com/ultimatile/JuliaPkgTemplatesCLI.git

# Install from a specific release tag (once available)
uv tool install git+https://github.com/ultimatile/JuliaPkgTemplatesCLI.git@v0.1.0
```

### From Source

Since this is an alpha release, the recommended installation method is from source:

```bash
git clone https://github.com/ultimatile/JuliaPkgTemplatesCLI.git
cd JuliaPkgTemplatesCLI
uv tool install .
```

## Prerequisites

- Python 3.8 or higher
- Julia 1.6 or higher
- PkgTemplates.jl installed in Julia
- mise (optional, for mise task integration)

## Usage

The primary command is `jtc create <package_name>`, which generates a new Julia package using PkgTemplates.jl.
The other commands is `jtc config`, which allows you to set user defaults for package creation.

Example usage:

```bash
# Show help
jtc --help

# Create a new Julia package with minimal options
jtc create MyPackage

# Create a package with specific author and output directory
jtc create MyPackage --author "Your Name" --output-dir ~/projects

# Create a package with specific template and license
jtc create MyPackage --template full --license Apache-2.0

# Create a package without documentation or CI
jtc create MyPackage --no-docs --no-ci

# Create a package with specific JuliaFormatter style
jtc create MyPackage --formatter-style blue

# Configure default settings (see Configuration section)
jtc config --author "Your Name" --license MIT --template standard

# Show current version
jtc --version
```

## Configuration

jtc supports user-configurable defaults to streamline package creation. Configuration is stored in `~/$XDG_CONFIG_HOME/jtc/config.toml` (default is `~/.config/jtc/config.toml`) following XDG Base Directory standards.

### Setting Defaults

```bash
# Set default author name
jtc config --author "Your Name"

# Set default license
jtc config --license Apache-2.0

# Set default template type
jtc config --template full

# Set default formatter style
jtc config --formatter-style blue

# Set multiple defaults at once
jtc config --author "Your Name" --license MIT --template standard --formatter-style sciml
```

### Configuration File Format

The configuration file uses TOML format:

```toml
[default]
author = "Your Name"
license = "MIT"
template = "standard"
formatter_style = "nostyle"
```

### Configuration Precedence

1. **Command-line options** (highest priority)
2. **Configuration file defaults**
3. **Built-in defaults** (lowest priority)

For example, if you have `author = "Config Author"` in your config file but run `jtc create MyPackage --author "CLI Author"`, the CLI argument takes precedence.

### Available Options

- **author**: Default author name for packages
- **license**: Default license type (`MIT`, `Apache-2.0`, `BSD-3-Clause`, `GPL-3.0`)
- **template**: Default template type (`minimal`, `standard`, `full`)
- **formatter_style**: Default JuliaFormatter style (`nostyle`, `sciml`, `blue`, `yas`)

### Configuration Location

Configuration files are stored in `~/.config/jtc/config.toml` (Linux/macOS).

If `XDG_CONFIG_HOME` environment variable is set, that location will be used instead.

## Alpha Release Notes

- This alpha version focuses on core package generation functionality
- Some advanced features may not be fully implemented
- Configuration options are subject to change
- Documentation and examples are still being developed
- Please report issues on the GitHub repository

## Development

For development setup:

```bash
git clone https://github.com/ultimatile/JuliaPkgTemplatesCLI.git
cd JuliaPkgTemplatesCLI
uv sync
uv run jtc # Run the command
uv run pytest  # Run tests
```
