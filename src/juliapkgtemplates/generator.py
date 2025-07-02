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


@dataclass
class PackageConfig:
    """Configuration for package creation"""

    template: str = "standard"
    license_type: Optional[str] = None
    julia_version: Optional[str] = None
    plugin_options: Optional[Dict[str, Dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, config_dict: Optional[Dict[str, Any]] = None) -> "PackageConfig":
        """Create PackageConfig from dictionary, ignoring unknown keys"""
        if config_dict is None:
            return cls()

        # Handle mixed input formats: direct plugin_options dict and dot notation from config files
        plugin_options = {}
        regular_config = {}

        for key, value in config_dict.items():
            if key == "plugin_options" and isinstance(value, dict):
                # Direct plugin_options dictionary from CLI
                plugin_options.update(value)
            elif "." in key:
                # Dot notation plugin option (e.g., from config file)
                plugin_name, option_name = key.split(".", 1)
                if plugin_name not in plugin_options:
                    plugin_options[plugin_name] = {}
                plugin_options[plugin_name][option_name] = value
            else:
                # This is a regular config option
                regular_config[key] = value

        # Ensure type safety by filtering to known dataclass fields
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_dict = {k: v for k, v in regular_config.items() if k in valid_keys}

        # Always set plugin_options (empty dict if no plugin options found)
        filtered_dict["plugin_options"] = plugin_options if plugin_options else {}

        return cls(**filtered_dict)


class JuliaPackageGenerator:
    """Julia package generator with PkgTemplates.jl and mise integration"""

    # Known PkgTemplates.jl plugins for CLI option generation
    KNOWN_PLUGINS = [
        "Git",
        "License",
        "Tests",
        "Formatter",
        "ProjectFile",
        "GitHubActions",
        "Codecov",
        "Documenter",
        "TagBot",
        "CompatHelper",
    ]

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
        """Convert CLI license names to PkgTemplates.jl format for interoperability"""
        mapped_license = self.LICENSE_MAPPING.get(license_name, license_name)
        if (
            mapped_license == license_name
            and license_name not in self.LICENSE_MAPPING.values()
        ):
            # Warn when license identifier may not be recognized by PkgTemplates.jl
            logging.warning(f"Unknown license '{license_name}', using as-is")
        return mapped_license

    def create_package(
        self,
        package_name: str,
        author: Optional[str],
        user: Optional[str],
        mail: Optional[str],
        output_dir: Path,
        config: Optional[PackageConfig] = None,
        verbose: bool = False,
    ) -> Path:
        """
        Create a new Julia package using PkgTemplates.jl

        Args:
            package_name: Name of the package
            author: Author name
            user: Git hosting username
            mail: Email address
            output_dir: Directory where package will be created
            config: PackageConfig instance with package creation settings

        Returns:
            Path to the created package directory
        """
        output_dir = Path(output_dir).resolve()
        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        # Use provided config or create default
        cfg = config if config is not None else PackageConfig()

        plugins = self._get_plugins(
            cfg.template,
            cfg.license_type,
            cfg.plugin_options,
        )

        package_dir = self._call_julia_generator(
            package_name,
            author,
            user,
            mail,
            output_dir,
            plugins,
            cfg.julia_version,
            verbose,
        )

        self._add_mise_config(package_dir, package_name)

        return package_dir

    def generate_julia_code(
        self,
        package_name: str,
        author: Optional[str],
        user: Optional[str],
        mail: Optional[str],
        output_dir: Path,
        config: Optional[PackageConfig] = None,
    ) -> str:
        """
        Generate Julia Template function code without executing it (for dry-run mode)

        Args:
            package_name: Name of the package
            author: Author name
            user: Git hosting username
            mail: Email address
            output_dir: Directory where package would be created
            config: PackageConfig instance with package creation settings

        Returns:
            String containing the Julia Template function code
        """
        # Use provided config or create default
        cfg = config if config is not None else PackageConfig()

        plugins = self._get_plugins(
            cfg.template,
            cfg.license_type,
            cfg.plugin_options,
        )

        return self._generate_julia_template_code(
            package_name, author, user, mail, output_dir, plugins, cfg.julia_version
        )

    def _get_plugins(
        self,
        template: str,
        license_type: Optional[str],
        plugin_options: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Assemble Julia plugin configuration based on template choice and user overrides"""
        if template not in self.TEMPLATE_CONFIGS:
            raise ValueError(
                f"Unknown template type: {template}. Available: {list(self.TEMPLATE_CONFIGS.keys())}"
            )

        config = self.TEMPLATE_CONFIGS[template]
        plugins = []

        # Map each plugin type to its configuration builder function
        plugin_builders = {
            "ProjectFile": lambda: self._build_project_file_plugin(plugin_options),
            "License": lambda: self._build_license_plugin(license_type, plugin_options),
            "Git": lambda: self._build_git_plugin(plugin_options),
            "Formatter": lambda: self._build_formatter_plugin(plugin_options),
            "Tests": lambda: self._build_tests_plugin(plugin_options),
            "GitHubActions": lambda: self._build_github_actions_plugin(plugin_options),
            "Codecov": lambda: self._build_codecov_plugin(plugin_options),
            "Documenter": lambda: self._build_documenter_plugin(plugin_options),
            "TagBot": lambda: self._build_tagbot_plugin(plugin_options),
            "CompatHelper": lambda: self._build_compathelper_plugin(plugin_options),
        }

        for plugin_name in config.plugins:
            if plugin_name in plugin_builders:
                plugin = plugin_builders[plugin_name]()
                if plugin:  # Exclude disabled or invalid plugins
                    plugins.append(plugin)

        return {
            "plugins": plugins,
        }

    def _build_project_file_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Generate ProjectFile plugin with semantic versioning constraints"""
        version = "0.0.1"  # Default follows semantic versioning convention

        # Get version from plugin options
        if plugin_options and "ProjectFile" in plugin_options:
            options = plugin_options["ProjectFile"]
            if "version" in options:
                version = options["version"]

        return f'ProjectFile(; version=v"{version}")'

    def _build_license_plugin(
        self,
        license_type: Optional[str],
        plugin_options: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Optional[str]:
        """Create License plugin when license is specified, deferring to PkgTemplates.jl defaults otherwise"""
        if not license_type:
            return None
        mapped_license = self._map_license(license_type)

        # Override with plugin options if provided
        if plugin_options and "License" in plugin_options:
            options = plugin_options["License"]
            if "name" in options:
                mapped_license = options["name"]

        return f'License(; name="{mapped_license}")'

    def _build_git_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure Git plugin with manifest handling and repository access method"""
        git_options = []

        # Configure default Git behavior for package development
        manifest = False
        ssh = False
        ignore_patterns = None

        # Get options from plugin options
        if plugin_options and "Git" in plugin_options:
            options = plugin_options["Git"]
            if "manifest" in options:
                manifest = options["manifest"]
            if "ssh" in options:
                ssh = options["ssh"]
            if "ignore" in options:
                ignore_patterns = options["ignore"]

        git_options.append(f"manifest={str(manifest).lower()}")

        if ssh:
            git_options.append("ssh=true")
        if ignore_patterns:
            # Support both list and comma-separated string formats from config
            if isinstance(ignore_patterns, list):
                patterns = [f'"{p}"' for p in ignore_patterns]
            else:
                patterns = [
                    f'"{p.strip()}"' for p in ignore_patterns.split(",") if p.strip()
                ]
            git_options.append(f"ignore=[{', '.join(patterns)}]")
        return f"Git(; {', '.join(git_options)})"

    def _build_formatter_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Build Formatter plugin configuration"""
        style = "nostyle"  # Default style

        # Get style from plugin options
        if plugin_options and "Formatter" in plugin_options:
            options = plugin_options["Formatter"]
            if "style" in options:
                style = options["style"]

        return f'Formatter(; style="{style}")'

    def _build_tests_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Optional[str]:
        """Configure testing framework with optional static analysis tools"""
        # Enable basic testing with optional quality assurance tools
        tests_aqua = False
        tests_jet = False
        tests_project = True

        # Get options from plugin options
        if plugin_options and "Tests" in plugin_options:
            options = plugin_options["Tests"]
            if "aqua" in options:
                tests_aqua = options["aqua"]
            if "jet" in options:
                tests_jet = options["jet"]
            if "project" in options:
                tests_project = options["project"]

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

    def _build_github_actions_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Optional[str]:
        """Enable GitHub Actions CI/CD integration for automated testing and deployment"""
        return "GitHubActions()"

    def _build_codecov_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Optional[str]:
        """Enable Codecov integration for test coverage reporting"""
        return "Codecov()"

    def _build_documenter_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Optional[str]:
        """Configure Documenter.jl with GitHub Actions for automated documentation builds"""
        return "Documenter{GitHubActions}()"

    def _build_tagbot_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Build TagBot plugin configuration"""
        return "TagBot()"

    def _build_compathelper_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Build CompatHelper plugin configuration"""
        return "CompatHelper()"

    def _generate_julia_template_code(
        self,
        package_name: str,
        author: Optional[str],
        user: Optional[str],
        mail: Optional[str],
        output_dir: Path,
        plugins: Dict[str, Any],
        julia_version: Optional[str] = None,
    ) -> str:
        """Generate Julia Template function code for visualization"""
        plugins_str = "[" + ", ".join(plugins["plugins"]) + "]"

        # Build the Julia Template function code
        julia_code = "using PkgTemplates\n\n"

        # Template constructor
        template_args = []

        # Add author if provided
        if author:
            template_args.append(f'authors=["{author}"]')

        # Add user if provided
        if user:
            template_args.append(f'user="{user}"')

        # Add mail if provided
        if mail:
            template_args.append(f'mail="{mail}"')

        # Add output directory
        template_args.append(f'dir="{output_dir}"')

        # Add julia version if provided
        if julia_version:
            # Normalize version format to ensure v-prefix compatibility with VersionNumber
            version_str = julia_version.lstrip("v")
            template_args.append(f'julia=v"{version_str}"')

        # Add plugins
        template_args.append(f"plugins={plugins_str}")

        julia_code += "t = Template(;\n"
        for i, arg in enumerate(template_args):
            julia_code += f"    {arg}"
            if i < len(template_args) - 1:
                julia_code += ","
            julia_code += "\n"
        julia_code += ")\n\n"

        # Package generation call
        julia_code += f't("{package_name}")\n'

        return julia_code

    def _call_julia_generator(
        self,
        package_name: str,
        author: Optional[str],
        user: Optional[str],
        mail: Optional[str],
        output_dir: Path,
        plugins: Dict[str, Any],
        julia_version: Optional[str] = None,
        verbose: bool = False,
    ) -> Path:
        """Execute PkgTemplates.jl package generation via subprocess interface"""
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
            if verbose:
                # In verbose mode, show Julia output in real-time
                _result = subprocess.run(cmd, text=True, check=True)
            else:
                # In normal mode, capture output for error handling
                _result = subprocess.run(
                    cmd, capture_output=True, text=True, check=True
                )

            package_dir = output_dir / package_name
            if not package_dir.exists():
                raise RuntimeError(f"Package directory not created: {package_dir}")

            return package_dir

        except subprocess.CalledProcessError as e:
            if verbose:
                # In verbose mode, output was already shown, just handle the error
                package_dir = output_dir / package_name
                if package_dir.exists():
                    return package_dir
                else:
                    raise RuntimeError(
                        f"Julia script failed with exit code {e.returncode}"
                    ) from e
            else:
                # In normal mode, parse error from captured output
                if "Error creating package:" in e.stdout or "Error:" in e.stdout:
                    error_pattern = re.compile(
                        r"(Error:|Error creating package:)\s*(.+)"
                    )
                    error_lines = error_pattern.findall(e.stdout)
                    if error_lines:
                        error_msg = error_lines[-1][1]
                    else:
                        error_msg = f"Julia script failed: {e.stdout}"
                    if "PkgTemplates" in e.stderr:
                        error_msg += "\nHint: Make sure PkgTemplates.jl is installed: julia -e 'using Pkg; Pkg.add(\"PkgTemplates\")'"
                    raise RuntimeError(error_msg) from e
                else:
                    # Handle case where Julia generates warnings but completes successfully
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
