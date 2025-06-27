"""
Julia package generator using PkgTemplates.jl and Jinja2
"""

import subprocess
from pathlib import Path
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader


class JuliaPackageGenerator:
    """Julia package generator with PkgTemplates.jl and mise integration"""

    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates"
        self.scripts_dir = Path(__file__).parent / "scripts"

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def create_package(
        self,
        package_name: str,
        author: str,
        output_dir: Path,
        template: str = "standard",
        license_type: str = "MIT",
        with_docs: bool = True,
        with_ci: bool = True,
        with_codecov: bool = True,
        formatter_style: str = "nostyle",
        julia_version: str = None,
        ssh: bool = False,
        ignore_patterns: str = None,
        tests_aqua: bool = False,
        tests_jet: bool = False,
        tests_project: bool = True,
        project_version: str = None,
        force_in_git_repo: bool = False,
    ) -> Path:
        """
        Create a new Julia package using PkgTemplates.jl

        Args:
            package_name: Name of the package
            author: Author name
            output_dir: Directory where package will be created
            template: Template type (minimal, standard, full)
            license_type: License type
            with_docs: Include documentation
            with_ci: Include CI/CD
            with_codecov: Include Codecov
            formatter_style: JuliaFormatter style (nostyle, sciml, blue, yas)
            julia_version: Julia version constraint for Template constructor
            ssh: Use SSH for Git operations
            ignore_patterns: Comma-separated list of patterns to ignore in Git
            tests_aqua: Enable Aqua.jl in Tests plugin
            tests_jet: Enable JET.jl in Tests plugin
            tests_project: Enable separate project for tests
            project_version: Initial version for ProjectFile plugin

        Returns:
            Path to the created package directory
        """
        # Validate inputs
        output_dir = Path(output_dir).resolve()
        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        # Check if output directory is inside a Git repository
        is_in_git_repo = self._is_in_git_repository(output_dir)
        if is_in_git_repo and not force_in_git_repo:
            raise RuntimeError(
                "Cannot create package inside existing Git repository. "
                "This may cause conflicts with PkgTemplates.jl. "
                "Use --force-in-git-repo to override (not recommended) or "
                "specify an output directory outside the Git repository."
            )

        # Determine plugins based on template type
        plugins = self._get_plugins(
            template,
            license_type,
            with_docs,
            with_ci,
            with_codecov,
            formatter_style,
            ssh,
            ignore_patterns,
            tests_aqua,
            tests_jet,
            tests_project,
            project_version,
            is_in_git_repo,
            force_in_git_repo,
        )

        # Call Julia script to create package
        package_dir = self._call_julia_generator(
            package_name, author, output_dir, plugins, julia_version
        )

        # Add mise configuration
        self._add_mise_config(package_dir, package_name)

        return package_dir

    def _get_plugins(
        self,
        template: str,
        license_type: str,
        with_docs: bool,
        with_ci: bool,
        with_codecov: bool,
        formatter_style: str,
        ssh: bool,
        ignore_patterns: str,
        tests_aqua: bool,
        tests_jet: bool,
        tests_project: bool,
        project_version: str,
        is_in_git_repo: bool,
        force_in_git_repo: bool,
    ) -> Dict[str, Any]:
        """Get PkgTemplates.jl plugins configuration"""
        base_plugins = []

        # Add ProjectFile plugin with version if specified
        if project_version:
            base_plugins.append(f'ProjectFile(; version=v"{project_version}")')
        else:
            base_plugins.append('ProjectFile(; version=v"0.0.1")')

        # Add License plugin
        base_plugins.append(f'License(; name="{license_type}")')

        # Add Git plugin if not in a Git repository, or if force flag is used
        if not is_in_git_repo or force_in_git_repo:
            git_options = ["manifest=true"]
            if ssh:
                git_options.append("ssh=true")
            if ignore_patterns:
                # Parse comma-separated patterns and format as Julia array
                patterns = [
                    f'"{p.strip()}"' for p in ignore_patterns.split(",") if p.strip()
                ]
                git_options.append(f"ignore=[{', '.join(patterns)}]")
            git_plugin = f"Git(; {', '.join(git_options)})"
            base_plugins.append(git_plugin)

        # Add Formatter plugin
        base_plugins.append(f'Formatter(; style="{formatter_style}")')

        # Add Tests plugin with aqua and jet options
        test_options = []
        if tests_project:
            test_options.append("project=true")
        if tests_aqua:
            test_options.append("aqua=true")
        if tests_jet:
            test_options.append("jet=true")
        if test_options:
            tests_plugin = f"Tests(; {', '.join(test_options)})"
            base_plugins.append(tests_plugin)

        if template == "minimal":
            plugins = base_plugins
        elif template == "standard":
            additional_plugins = []
            if with_ci and (not is_in_git_repo or force_in_git_repo):
                additional_plugins.append("GitHubActions()")
            if with_codecov and (not is_in_git_repo or force_in_git_repo):
                additional_plugins.append("Codecov()")
            plugins = base_plugins + additional_plugins
        elif template == "full":
            additional_plugins = []
            if with_ci and (not is_in_git_repo or force_in_git_repo):
                additional_plugins.append("GitHubActions()")
            if with_codecov and (not is_in_git_repo or force_in_git_repo):
                additional_plugins.append("Codecov()")
            if with_docs and (not is_in_git_repo or force_in_git_repo):
                additional_plugins.append("Documenter{GitHubActions}()")
            if not is_in_git_repo or force_in_git_repo:
                additional_plugins.extend(["TagBot()", "CompatHelper()"])
            plugins = base_plugins + additional_plugins
        else:
            raise ValueError(f"Unknown template type: {template}")

        # Filter out None values
        plugins = [p for p in plugins if p is not None]

        return {
            "plugins": plugins,
            "license_type": license_type,
            "with_docs": with_docs,
            "with_ci": with_ci,
            "with_codecov": with_codecov,
        }

    def _call_julia_generator(
        self,
        package_name: str,
        author: str,
        output_dir: Path,
        plugins: Dict[str, Any],
        julia_version: str = None,
    ) -> Path:
        """Call Julia script to generate package"""
        julia_script = self.scripts_dir / "pkg_generator.jl"

        if not julia_script.exists():
            raise FileNotFoundError(f"Julia script not found: {julia_script}")

        # Convert plugins to Julia array format
        plugins_str = "[" + ", ".join(plugins["plugins"]) + "]"

        # Call Julia script
        cmd = [
            "julia",
            str(julia_script),
            package_name,
            author,
            str(output_dir),
            plugins_str,
        ]

        # Add Julia version if specified
        if julia_version:
            cmd.append(julia_version)

        try:
            _ = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Parse output to get package directory
            package_dir = output_dir / package_name
            if not package_dir.exists():
                raise RuntimeError(f"Package directory not created: {package_dir}")

            return package_dir

        except subprocess.CalledProcessError as e:
            # Check if the error is actually a failure by looking for error indicators
            if "Error creating package:" in e.stdout or "Error:" in e.stdout:
                # Extract the actual error message from Julia output
                lines = e.stdout.strip().split("\n")
                error_lines = [
                    line
                    for line in lines
                    if line.startswith("Error:") or "Error creating package:" in line
                ]

                if error_lines:
                    # Use the actual Julia error message without prefix
                    error_msg = error_lines[-1]  # Use the last error message
                    if error_msg.startswith("Error: "):
                        error_msg = error_msg[7:]  # Remove "Error: " prefix
                    elif "Error creating package: " in error_msg:
                        error_msg = error_msg.split("Error creating package: ", 1)[1]
                else:
                    error_msg = f"Julia script failed: {e.stdout}"

                if "PkgTemplates" in e.stderr:
                    error_msg += "\nHint: Make sure PkgTemplates.jl is installed: julia -e 'using Pkg; Pkg.add(\"PkgTemplates\")'"
                raise RuntimeError(error_msg) from e
            else:
                # Package might have been created successfully despite stderr output
                package_dir = output_dir / package_name
                if package_dir.exists():
                    return package_dir
                else:
                    error_msg = f"Julia script failed: {e.stderr}"
                    raise RuntimeError(error_msg) from e
        except FileNotFoundError:
            raise RuntimeError(
                "Julia not found. Please install Julia and ensure it's in your PATH."
            )

    def _add_mise_config(self, package_dir: Path, package_name: str) -> None:
        """Add mise configuration to the package"""
        template = self.jinja_env.get_template("mise.toml.j2")

        mise_content = template.render(package_name=package_name, project_dir=".")

        mise_file = package_dir / ".mise.toml"
        mise_file.write_text(mise_content)

    @staticmethod
    def check_dependencies() -> Dict[str, bool]:
        """Check if required dependencies are available"""
        dependencies = {}

        # Check Julia
        try:
            _ = subprocess.run(["julia", "--version"], capture_output=True, check=True)
            dependencies["julia"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            dependencies["julia"] = False

        # Check PkgTemplates.jl
        try:
            _ = subprocess.run(
                ["julia", "-e", "using PkgTemplates"], capture_output=True, check=True
            )
            dependencies["pkgtemplates"] = True
        except subprocess.CalledProcessError:
            dependencies["pkgtemplates"] = False

        # Check mise
        try:
            _ = subprocess.run(["mise", "--version"], capture_output=True, check=True)
            dependencies["mise"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            dependencies["mise"] = False

        return dependencies

    @staticmethod
    def _is_in_git_repository(path: Path) -> bool:
        """Check if the given path is inside a Git repository"""
        current_path = path.resolve()

        # Walk up the directory tree looking for .git directory
        while current_path != current_path.parent:
            if (current_path / ".git").exists():
                return True
            current_path = current_path.parent

        return False
