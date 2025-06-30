"""
Julia package generator using PkgTemplates.jl and Jinja2
"""

import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, List

from jinja2 import Environment, FileSystemLoader


@dataclass(frozen=True)
class TemplateConfig:
    """Configuration for a package template"""

    plugins: List[str]

    def includes(self, plugin: str) -> bool:
        """Check if template includes a specific plugin"""
        return plugin in self.plugins


class JuliaPackageGenerator:
    """Julia package generator with PkgTemplates.jl and mise integration"""

    # Map user-friendly license names to PkgTemplates.jl license identifiers
    LICENSE_MAPPING = {
        "MIT": "MIT",
        "Apache": "ASL",
        "BSD2": "BSD2",
        "BSD3": "BSD3",
        "GPL2": "GPL-2.0+",
        "GPL3": "GPL-3.0+",
        "MPL": "MPL",
        "ISC": "ISC",
        "LGPL2": "LGPL-2.1+",
        "LGPL3": "LGPL-3.0+",
        "AGPL3": "AGPL-3.0+",
        "EUPL": "EUPL-1.2+",
    }

    # Template configurations mapping template names to their plugin lists (order preserved)
    TEMPLATE_CONFIGS = {
        "minimal": TemplateConfig(
            plugins=["ProjectFile", "License", "Git", "Formatter", "Tests"]
        ),
        "standard": TemplateConfig(
            plugins=[
                "ProjectFile",
                "License",
                "Git",
                "Formatter",
                "Tests",
                "GitHubActions",
                "Codecov",
            ]
        ),
        "full": TemplateConfig(
            plugins=[
                "ProjectFile",
                "License",
                "Git",
                "Formatter",
                "Tests",
                "GitHubActions",
                "Codecov",
                "Documenter",
                "TagBot",
                "CompatHelper",
            ]
        ),
    }

    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates"
        self.scripts_dir = Path(__file__).parent / "scripts"

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _map_license(self, license_name: str) -> str:
        """Map user-friendly license name to PkgTemplates.jl identifier"""
        mapped_license = self.LICENSE_MAPPING.get(license_name, license_name)
        if (
            mapped_license == license_name
            and license_name not in self.LICENSE_MAPPING.values()
        ):
            # If no mapping found and it's not a valid PkgTemplates.jl license, warn
            logging.warning(f"Unknown license '{license_name}', using as-is")
        return mapped_license

    def create_package(
        self,
        package_name: str,
        author: Optional[str],
        user: Optional[str],
        mail: Optional[str],
        output_dir: Path,
        template: str = "standard",
        license_type: Optional[str] = None,
        with_docs: bool = True,
        with_ci: bool = True,
        with_codecov: bool = True,
        formatter_style: str = "nostyle",
        julia_version: Optional[str] = None,
        ssh: bool = False,
        ignore_patterns: Optional[str] = None,
        tests_aqua: bool = False,
        tests_jet: bool = False,
        tests_project: bool = True,
        project_version: Optional[str] = None,
    ) -> Path:
        """
        Create a new Julia package using PkgTemplates.jl

        Args:
            package_name: Name of the package
            author: Author name
            user: Git hosting username
            mail: Email address
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
        output_dir = Path(output_dir).resolve()
        if not output_dir.exists():
            output_dir.mkdir(parents=True)

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
        )

        package_dir = self._call_julia_generator(
            package_name, author, user, mail, output_dir, plugins, julia_version
        )

        self._add_mise_config(package_dir, package_name)

        return package_dir

    def _get_plugins(
        self,
        template: str,
        license_type: Optional[str],
        with_docs: bool,
        with_ci: bool,
        with_codecov: bool,
        formatter_style: str,
        ssh: bool,
        ignore_patterns: Optional[str],
        tests_aqua: bool,
        tests_jet: bool,
        tests_project: bool,
        project_version: Optional[str],
    ) -> Dict[str, Any]:
        """Get PkgTemplates.jl plugins configuration using template-based approach"""
        if template not in self.TEMPLATE_CONFIGS:
            raise ValueError(
                f"Unknown template type: {template}. Available: {list(self.TEMPLATE_CONFIGS.keys())}"
            )

        config = self.TEMPLATE_CONFIGS[template]
        plugins = []

        # Build plugins based on template configuration and user preferences
        plugin_builders = {
            "ProjectFile": lambda: self._build_project_file_plugin(project_version),
            "License": lambda: self._build_license_plugin(license_type),
            "Git": lambda: self._build_git_plugin(ssh, ignore_patterns),
            "Formatter": lambda: self._build_formatter_plugin(formatter_style),
            "Tests": lambda: self._build_tests_plugin(
                tests_aqua, tests_jet, tests_project
            ),
            "GitHubActions": lambda: self._build_github_actions_plugin(with_ci),
            "Codecov": lambda: self._build_codecov_plugin(with_codecov),
            "Documenter": lambda: self._build_documenter_plugin(with_docs),
            "TagBot": lambda: self._build_tagbot_plugin(),
            "CompatHelper": lambda: self._build_compathelper_plugin(),
        }

        for plugin_name in config.plugins:
            if plugin_name in plugin_builders:
                plugin = plugin_builders[plugin_name]()
                if plugin:  # Only add non-None plugins
                    plugins.append(plugin)

        return {
            "plugins": plugins,
            "license_type": license_type,
            "with_docs": with_docs,
            "with_ci": with_ci,
            "with_codecov": with_codecov,
        }

    def _build_project_file_plugin(self, project_version: Optional[str]) -> str:
        """Build ProjectFile plugin configuration"""
        version = project_version or "0.0.1"
        return f'ProjectFile(; version=v"{version}")'

    def _build_license_plugin(self, license_type: Optional[str]) -> Optional[str]:
        """Build License plugin configuration"""
        if not license_type:
            return None
        mapped_license = self._map_license(license_type)
        return f'License(; name="{mapped_license}")'

    def _build_git_plugin(self, ssh: bool, ignore_patterns: Optional[str]) -> str:
        """Build Git plugin configuration"""
        git_options = ["manifest=true"]
        if ssh:
            git_options.append("ssh=true")
        if ignore_patterns:
            patterns = [
                f'"{p.strip()}"' for p in ignore_patterns.split(",") if p.strip()
            ]
            git_options.append(f"ignore=[{', '.join(patterns)}]")
        return f"Git(; {', '.join(git_options)})"

    def _build_formatter_plugin(self, formatter_style: str) -> str:
        """Build Formatter plugin configuration"""
        return f'Formatter(; style="{formatter_style}")'

    def _build_tests_plugin(
        self, tests_aqua: bool, tests_jet: bool, tests_project: bool
    ) -> Optional[str]:
        """Build Tests plugin configuration"""
        test_options = []
        if tests_project:
            test_options.append("project=true")
        if tests_aqua:
            test_options.append("aqua=true")
        if tests_jet:
            test_options.append("jet=true")
        if test_options:
            return f"Tests(; {', '.join(test_options)})"
        return None

    def _build_github_actions_plugin(self, with_ci: bool) -> Optional[str]:
        """Build GitHubActions plugin configuration"""
        return "GitHubActions()" if with_ci else None

    def _build_codecov_plugin(self, with_codecov: bool) -> Optional[str]:
        """Build Codecov plugin configuration"""
        return "Codecov()" if with_codecov else None

    def _build_documenter_plugin(self, with_docs: bool) -> Optional[str]:
        """Build Documenter plugin configuration"""
        return "Documenter{GitHubActions}()" if with_docs else None

    def _build_tagbot_plugin(self) -> str:
        """Build TagBot plugin configuration"""
        return "TagBot()"

    def _build_compathelper_plugin(self) -> str:
        """Build CompatHelper plugin configuration"""
        return "CompatHelper()"

    def _call_julia_generator(
        self,
        package_name: str,
        author: Optional[str],
        user: Optional[str],
        mail: Optional[str],
        output_dir: Path,
        plugins: Dict[str, Any],
        julia_version: Optional[str] = None,
    ) -> Path:
        """Call Julia script to generate package"""
        julia_script = self.scripts_dir / "pkg_generator.jl"

        if not julia_script.exists():
            raise FileNotFoundError(f"Julia script not found: {julia_script}")

        plugins_str = "[" + ", ".join(plugins["plugins"]) + "]"

        cmd = [
            "julia",
            str(julia_script),
            package_name,
            author or "",
            user or "",
            mail or "",
            str(output_dir),
            plugins_str,
        ]

        if julia_version:
            cmd.append(julia_version)

        try:
            _ = subprocess.run(cmd, capture_output=True, text=True, check=True)

            package_dir = output_dir / package_name
            if not package_dir.exists():
                raise RuntimeError(f"Package directory not created: {package_dir}")

            return package_dir

        except subprocess.CalledProcessError as e:
            if "Error creating package:" in e.stdout or "Error:" in e.stdout:
                error_pattern = re.compile(r"(Error:|Error creating package:)\s*(.+)")
                error_lines = error_pattern.findall(e.stdout)
                if error_lines:
                    error_msg = error_lines[-1][1]
                else:
                    error_msg = f"Julia script failed: {e.stdout}"
                if "PkgTemplates" in e.stderr:
                    error_msg += "\nHint: Make sure PkgTemplates.jl is installed: julia -e 'using Pkg; Pkg.add(\"PkgTemplates\")'"
                raise RuntimeError(error_msg) from e
            else:
                # PkgTemplates.jl may output warnings to stderr but still succeed
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

        try:
            _ = subprocess.run(["julia", "--version"], capture_output=True, check=True)
            dependencies["julia"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            dependencies["julia"] = False

        try:
            _ = subprocess.run(
                ["julia", "-e", "using PkgTemplates"], capture_output=True, check=True
            )
            dependencies["pkgtemplates"] = True
        except subprocess.CalledProcessError:
            dependencies["pkgtemplates"] = False

        try:
            _ = subprocess.run(["mise", "--version"], capture_output=True, check=True)
            dependencies["mise"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            dependencies["mise"] = False

        return dependencies
