# CHANGELOG


## v0.1.0-rc.1 (2025-06-30)

### Bug Fixes

- **ci**: Branch 'dev' isn't in any release groups; no release will be made
  ([`4477770`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/44777705a3a293987ef475e95cc57aee28b8f467))


## v0.0.2 (2025-06-29)

### Bug Fixes

- Fix(ci): prepare for semantic release with squash merge
  ([#5](https://github.com/ultimatile/JuliaPkgTemplatesCLI/pull/5),
  [`6e9b7bb`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/6e9b7bb44e171df6e8627fe255f5e7d9547ac2c4))

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

* feat(cli): add --mail option for email metadata

- Add --mail/-m option to create and config commands - Update Julia script to accept mail parameter
  as 4th argument - Add mail parameter handling in generator with git config fallback - Update
  function signatures to include mail parameter - Ensure mail parameter is conditionally passed to
  PkgTemplates.jl Template() - Update basic tests to handle new mail parameter

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>

* chore: update uv.lock

* test: add comprehensive tests for --mail option and git config fallback

* docs(cli): improve help messages for author/user/mail options

* refactor(pkg_generator): modularize plugin parsing with registry pattern

* test: isolate config in minimal template workflow test

- Add isolated_config fixture to test_minimal_template_workflow - Ensure test runs with empty config
  to properly validate no-license behavior - Maintains separation between config defaults testing
  and PkgTemplates.jl delegation testing - Fixes test failure when user config contains default
  license setting

* chore(ci): add new GHA to rename the PR title for releases

* fix(ci): add setup of git config for tests

* fix(ci): configure PSR to bump semver with squash merge workflow

* fix(ci): fix deperecation warning of PSR

* fix(ci): correct semantic-release branches configuration format

Convert branches from TOML array of tables to dictionary format to resolve semantic-release
  validation error

* fixup! fix(ci): configure PSR to bump semver with squash merge workflow

---------

Co-authored-by: Claude <noreply@anthropic.com>

- **ci**: Add setup of git config for tests
  ([`ea8c73d`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/ea8c73dd8574bdf3573189d5eba127542575476c))

- **ci**: Configure PSR to bump semver with squash merge workflow
  ([`24a8fb9`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/24a8fb95b3491f7a80ad8d738a51c77a4e87f20a))

- **ci**: Configure PSR to bump semver with squash merge workflow
  ([`2e5ad17`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/2e5ad17f4d58bc458a55899b6d864e6fd65f14b6))

- **ci**: Configure PSR to bump semver with squash merge workflow
  ([`ecdaeee`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/ecdaeee908a7eb67490526e56ae602ed83bc8705))

- **ci**: Prepare for semantic release with squash merge
  ([#4](https://github.com/ultimatile/JuliaPkgTemplatesCLI/pull/4),
  [`c28f4a6`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/c28f4a6609d96359aefdd9be66a933ea10a065a5))

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

* feat(cli): add --mail option for email metadata

- Add --mail/-m option to create and config commands - Update Julia script to accept mail parameter
  as 4th argument - Add mail parameter handling in generator with git config fallback - Update
  function signatures to include mail parameter - Ensure mail parameter is conditionally passed to
  PkgTemplates.jl Template() - Update basic tests to handle new mail parameter

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>

* chore: update uv.lock

* test: add comprehensive tests for --mail option and git config fallback

* docs(cli): improve help messages for author/user/mail options

* refactor(pkg_generator): modularize plugin parsing with registry pattern

* test: isolate config in minimal template workflow test

- Add isolated_config fixture to test_minimal_template_workflow - Ensure test runs with empty config
  to properly validate no-license behavior - Maintains separation between config defaults testing
  and PkgTemplates.jl delegation testing - Fixes test failure when user config contains default
  license setting

* chore(ci): add new GHA to rename the PR title for releases

* fix(ci): add setup of git config for tests

* fix(ci): configure PSR to bump semver with squash merge workflow

* fix(ci): fix deperecation warning of PSR

* fix(ci): correct semantic-release branches configuration format

Convert branches from TOML array of tables to dictionary format to resolve semantic-release
  validation error

---------

Co-authored-by: Claude <noreply@anthropic.com>

- **ci**: Prepare for semantic release with squash merge
  ([#4](https://github.com/ultimatile/JuliaPkgTemplatesCLI/pull/4),
  [`5192bc1`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/5192bc137f3e543bc3758e7c32326ad6a27f8d75))

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

* feat(cli): add --mail option for email metadata

- Add --mail/-m option to create and config commands - Update Julia script to accept mail parameter
  as 4th argument - Add mail parameter handling in generator with git config fallback - Update
  function signatures to include mail parameter - Ensure mail parameter is conditionally passed to
  PkgTemplates.jl Template() - Update basic tests to handle new mail parameter

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>

* chore: update uv.lock

* test: add comprehensive tests for --mail option and git config fallback

* docs(cli): improve help messages for author/user/mail options

* refactor(pkg_generator): modularize plugin parsing with registry pattern

* test: isolate config in minimal template workflow test

- Add isolated_config fixture to test_minimal_template_workflow - Ensure test runs with empty config
  to properly validate no-license behavior - Maintains separation between config defaults testing
  and PkgTemplates.jl delegation testing - Fixes test failure when user config contains default
  license setting

* chore(ci): add new GHA to rename the PR title for releases

* fix(ci): add setup of git config for tests

* fix(ci): configure PSR to bump semver with squash merge workflow

* fix(ci): fix deperecation warning of PSR

* fix(ci): correct semantic-release branches configuration format

Convert branches from TOML array of tables to dictionary format to resolve semantic-release
  validation error

---------

Co-authored-by: Claude <noreply@anthropic.com>

- **pkg_generator**: Fix author and mail option to reproduce PkgTempltes.jl's behavior
  ([`75b6d0e`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/75b6d0e03437f5afb8ce733e984cbb2e78f5959a))

### Chores

- **ci**: Add new GHA to rename the PR title for releases
  ([`16829a6`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/16829a6cfe764230cdbe24833fe83b049e488c79))

### Documentation

- **cli**: Improve help messages for author/user/mail options
  ([`f272e61`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/f272e613fab0cd2d8198cb39075b01446e26d817))

### Features

- **cli**: Add --mail option for email metadata
  ([`7e4cdca`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/7e4cdca5ba89e1a7c6d3c41197933030717552ad))

- Add --mail/-m option to create and config commands - Update Julia script to accept mail parameter
  as 4th argument - Add mail parameter handling in generator with git config fallback - Update
  function signatures to include mail parameter - Ensure mail parameter is conditionally passed to
  PkgTemplates.jl Template() - Update basic tests to handle new mail parameter

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>

### Refactoring

- **pkg_generator**: Modularize plugin parsing with registry pattern
  ([`d3ca5c7`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/d3ca5c78e5153588c07b8ae8b835140b0f41ef6b))

### Testing

- **pkg_generator**: Fix author and mail option to reproduce PkgTempltes.jl's behavior
  ([`ee84132`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/ee84132fd86f20ef8cda76b718fe739934f01128))


## v0.0.1 (2025-06-27)

### Bug Fixes

- Lint
  ([`f99d587`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/f99d5876f1e7d1c21ea2f465f74f91880c37534a))

- Rename old config filename
  ([`967148d`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/967148d98c87e5c95751ca8501efbae9de41a4d6))

- Replace unused variable `foo` with `_`
  ([`b469533`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/b469533ba64e06882b2119e97f1bc38c885eb665))

- Resolve pyright type error
  ([`7feddeb`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/7feddeb914d2085bd79296f37d0af15117327f7a))

- **ci**: Add semantic-release configuration
  ([`059c28d`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/059c28d6d4f06408f0bfe3bf533707f616e0ea2f))

- Add python-semantic-release dependency - Configure semantic-release with version tracking - Set up
  changelog generation with proper commit patterns - Exclude maintenance commits from changelog

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

- **ci**: Update GHA for semantic-release
  ([`54e7888`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/54e78885fa2607fc53458230af306c97c1f6102f))

- **config**: Use more XDG_CONFIG_HOME compatible path
  ([`a4ea2e6`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/a4ea2e6e2368c5e21f69ae7f73839e8676352390))

- **generator**: Remove Develop() plugin to prevent Julia environment conflicts
  ([`11429f8`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/11429f8e932b43d0e18b8bbd0bca493aeb26f2b9))

- **generator**: Resolve Julia script path resolution issue
  ([`5f6df2c`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/5f6df2c8eecfc9e684165266e1ebd959630948da))

- **generator**: Use warning message instead of print
  ([`a4bd010`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/a4bd010f459900593268c0ed5ec3bf0c7d3a67e8))

- **pkg_generator**: Correctly reject package names according to Julia’s naming conventions
  ([`cb25903`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/cb25903f589ce3832c0a37a1f3dd7ea4b37035f7))

Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>

- **pkg_generator**: Delegate package name validation to PkgTemplates.jl
  ([`b075add`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/b075add68469ca84e943d4ba5a0386aa16c5164e))

- **pkg_generator**: Remove pkg_generator.jl at the old path
  ([`979d809`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/979d80939b2ced70fa83782b51642127c1c97e91))

- **pkg_generator**: Resolve MIT license MethodError and improve error handling
  ([`55dd2bc`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/55dd2bce7a804cdf1377fbbd1d5cde2f57007a8e))

- **test**: Resolve pytest failures and pyright type errors
  ([`9fc3ff2`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/9fc3ff274229625dba11ed4fd76cc3bb628306ae))

- **tests**: Remove unnecessary file
  ([`c19b719`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/c19b719f7fc202944ed9c7284bd6385a01fa203f))

- **tests**: Resolve 9 failing pytest cases for complete test suite
  ([`1119aff`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/1119aff5a97288487137d44b1aa63d9a1d9a2407))

- Fix tomli_w import mock in test_save_config_fallback - Correct CalledProcessError initialization
  in generator error tests - Remove incorrect .jl suffixes from package directory creation in
  integration tests - Handle macOS /private path prefix resolution in subprocess call assertions -
  Mock load_config to prevent test isolation issues in interactive workflow - All 45 tests now pass
  successfully with uv run pytest

- **tests**: Resolve deps for pytest
  ([`9a9ff1c`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/9a9ff1cb98af4d7d00b0f1ff4f8597b6da7f6766))

### Features

- Migrate to Python 3.11+ and consolidate TOML handling
  ([`bc2d814`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/bc2d814a4acc14bf4353fb875a88db84144b2d4c))

- Drop support for Python 3.8-3.10, require Python 3.11+ - Remove conditional tomli dependency and
  use built-in tomllib - Update CI matrix to test only Python 3.11 and 3.12 - Simplify config
  loading logic by removing fallback imports - Update project classifiers to reflect new Python
  version support

- Remove --force-in-git-repo option and git repository detection
  ([`bed7994`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/bed799474d05cd4d82cad18b956e164505bb8291))

- Separate author and user parameters to enable PkgTemplates.jl fallback
  ([`22c1226`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/22c12268e4351190af27772ac836bd8847d09584))

- **cli**: Implement XDG config directory support and improved config handling
  ([`24c9ea9`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/24c9ea9db64a9c6ef46cae8800e6228e8342211d))

- **cli**: Improve help text with dynamic config
  ([`0adc6cf`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/0adc6cfcb524e9e8512ea525450cfa57573518f1))

- **formatter**: Add JuliaFormatter plugin support
  ([`5c4e9d7`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/5c4e9d7e7392504ca4e355e795bb518e2900d74f))

Add --formatter-style option to configure JuliaFormatter styles (nostyle, sciml, blue, yas) in
  generated packages using PkgTemplates.jl Formatter plugin.

- **license**: Implement user-friendly license mapping system
  ([`231ecb7`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/231ecb7ed9796519837f227799f754cc519cb0ad))

### Refactoring

- Extract common help text generation logic
  ([`db4cf34`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/db4cf3446fd4cfdec093c07d81ccede78411eace))

- **generator**: Improve error parsing with regex
  ([`d0d12cf`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/d0d12cf13507cb6a3c8db24df34bc7fd1215b78b))

- **license**: Delegate license fallback to PkgTemplates.jl default
  ([`e9d352f`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/e9d352f5b3981ec0de206aae401fa86903213f7a))

- **pkg_generator**: Use table form instead of many elseif
  ([`d7ffc0f`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/d7ffc0fa909103fd8fbf053a72b790c9dc4dc05f))

- **test**: Remove duplicate isolated_dir fixture from test_helpers.py
  ([`60ca050`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/60ca05006785909d1ca277c18e7a8248d2916c0a))

### Testing

- **config**: Isolate user config files during tests
  ([`fbe82a6`](https://github.com/ultimatile/JuliaPkgTemplatesCLI/commit/fbe82a683e7d3a2fdbf0b67384d3d745dcca1b37))
