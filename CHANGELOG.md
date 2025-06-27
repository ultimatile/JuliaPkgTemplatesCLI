# CHANGELOG


## v0.0.1 (2025-06-27)

### Bug Fixes

- **ci**: Add semantic-release configuration and dependencies
  ([#2](https://github.com/ultimatile/JuliaPkgTemplatesCLI/pull/2),
  [`991fb7e`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/991fb7eb52ac7be6069de534986a3496944ba15c))

* chore: initial setup

* fix(generator): remove Develop() plugin to prevent Julia environment conflicts

* feat(cli): implement XDG config directory support and improved config handling

* fix(generator): resolve Julia script path resolution issue

* fix(pkg_generator): remove pkg_generator.jl at the old path

* fix: lint

* refactor(pkg_generator): use table form instead of many elseif

* chore: fix URLs

* chore: fix package description

* test: add comprehensive pytest suite with 45 tests

- Add pytest configuration and fixtures in tests/conftest.py - Create CLI tests covering config
  management, create/config commands - Add generator tests for plugin configuration and Julia
  integration - Include integration tests for end-to-end workflows - Add test dependencies to
  pyproject.toml (pytest, pytest-mock) - Create run_tests.py helper script for easier test execution
  - Tests cover validation, error handling, mocking, and template logic

* fix(tests): resolve 9 failing pytest cases for complete test suite

- Fix tomli_w import mock in test_save_config_fallback - Correct CalledProcessError initialization
  in generator error tests - Remove incorrect .jl suffixes from package directory creation in
  integration tests - Handle macOS /private path prefix resolution in subprocess call assertions -
  Mock load_config to prevent test isolation issues in interactive workflow - All 45 tests now pass
  successfully with uv run pytest

* feat(formatter): add JuliaFormatter plugin support

Add --formatter-style option to configure JuliaFormatter styles (nostyle, sciml, blue, yas) in
  generated packages using PkgTemplates.jl Formatter plugin.

* fix(tests): resolve deps for pytest

* fix(tests): remove unnecessary file

* chore: rename the package

* fix(config): use more XDG_CONFIG_HOME compatible path

* chore: update README.md for alpha release

* fix(pkg_generator): correctly reject package names according to Julia’s naming conventions

Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>

* fix(pkg_generator): delegate package name validation to PkgTemplates.jl

* fix(pkg_generator): resolve MIT license MethodError and improve error handling

* reject in-Git-repo by default, add --force-in-git-repo, and restructure tests into
  unit/integration/e2e

* feat(cli): improve help text with dynamic config

* fix: replace unused variable `foo` with `_`

* fix: resolve pyright type error

* fix(ci): update GHA for semantic-release

* feat: migrate to Python 3.11+ and consolidate TOML handling

- Drop support for Python 3.8-3.10, require Python 3.11+ - Remove conditional tomli dependency and
  use built-in tomllib - Update CI matrix to test only Python 3.11 and 3.12 - Simplify config
  loading logic by removing fallback imports - Update project classifiers to reflect new Python
  version support

* fix(test): resolve pytest failures and pyright type errors

* chore: update README.md

* feat(license): implement user-friendly license mapping system

* test(config): isolate user config files during tests

* feat: remove --force-in-git-repo option and git repository detection

* chore: add pre-commit for ruff check and ruff format

* feat: separate author and user parameters to enable PkgTemplates.jl fallback

* docs: improve user option help text of user option

* refactor: extract common help text generation logic

* style: apply code formatting improvements

* fix(generator): use warning message instead of print

* refactor(generator): improve error parsing with regex

* chore: delete unnecessary comments and improve comments

* refactor(license): delegate license fallback to PkgTemplates.jl default

* refactor(test): remove duplicate isolated_dir fixture from test_helpers.py

* fix: rename old config filename

* fix(ci): add semantic-release configuration

- Add python-semantic-release dependency - Configure semantic-release with version tracking - Set up
  changelog generation with proper commit patterns - Exclude maintenance commits from changelog

---------
