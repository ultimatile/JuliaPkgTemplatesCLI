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

    enabled_plugins: Optional[List[str]] = None
    license_type: Optional[str] = None
    julia_version: Optional[str] = None
    plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    mise_filename_base: str = ".mise"
    with_mise: bool = True

    def __post_init__(self):
        if self.enabled_plugins is None:
            self.enabled_plugins = []

    @classmethod
    def from_dict(cls, config_dict: Optional[Dict[str, Any]] = None) -> "PackageConfig":
        """Create PackageConfig from dictionary, ignoring unknown keys"""
        if config_dict is None:
            return cls(plugin_options={})

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

        # Handle enabled_plugins as a list
        if "enabled_plugins" in filtered_dict and isinstance(
            filtered_dict["enabled_plugins"], str
        ):
            # Convert comma-separated string to list
            filtered_dict["enabled_plugins"] = [
                p.strip()
                for p in filtered_dict["enabled_plugins"].split(",")
                if p.strip()
            ]

        # Always set plugin_options (empty dict if no plugin options found)
        filtered_dict["plugin_options"] = plugin_options if plugin_options else {}

        return cls(**filtered_dict)


class JuliaPackageGenerator:
    """Julia package generator with PkgTemplates.jl and mise integration"""

    # Known PkgTemplates.jl plugins for CLI option generation
    KNOWN_PLUGINS = [
        # Core plugins
        "Git",
        "License",
        "Tests",
        "Formatter",
        "ProjectFile",
        "SrcDir",
        "Readme",
        # CI/CD plugins
        "GitHubActions",
        "AppVeyor",
        "CirrusCI",
        "DroneCI",
        "GitLabCI",
        "TravisCI",
        # Code coverage plugins
        "Codecov",
        "Coveralls",
        # Documentation plugins
        "Documenter",
        # Automation plugins
        "TagBot",
        "CompatHelper",
        "Dependabot",
        # Badge plugins
        "BlueStyleBadge",
        "ColPracBadge",
        "PkgEvalBadge",
        # Miscellaneous plugins
        "Develop",
        "Citation",
        "RegisterAction",
        "CodeOwners",
        "PkgBenchmark",
        "Runic",
    ]

    # Map user-friendly license names to PkgTemplates.jl license identifiers
    LICENSE_MAPPING = {
        "Apache": "ASL",
        "GPL2": "GPL-2.0+",
        "GPL3": "GPL-3.0+",
        "LGPL2": "LGPL-2.1+",
        "LGPL3": "LGPL-3.0+",
        "AGPL3": "AGPL-3.0+",
        "EUPL": "EUPL-1.2+",
    }

    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates"

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=False,
            lstrip_blocks=False,
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
        # Handle output directory path resolution
        output_dir = Path(output_dir)
        if not output_dir.is_absolute():
            # For relative paths, resolve them relative to current working directory
            output_dir = Path.cwd() / output_dir
        output_dir = output_dir.resolve()

        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        # Use provided config or create default
        cfg = config if config is not None else PackageConfig()

        plugins = self._get_plugins(
            cfg.enabled_plugins,
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

        if cfg.with_mise:
            self._add_mise_config(package_dir, package_name, cfg.mise_filename_base)

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
        # Handle output directory path resolution
        output_dir = Path(output_dir)
        if not output_dir.is_absolute():
            # For relative paths, resolve them relative to current working directory
            output_dir = Path.cwd() / output_dir
        output_dir = output_dir.resolve()

        # Use provided config or create default
        cfg = config if config is not None else PackageConfig()

        plugins = self._get_plugins(
            cfg.enabled_plugins,
            cfg.license_type,
            cfg.plugin_options,
        )

        return self._generate_julia_template_code(
            package_name, author, user, mail, output_dir, plugins, cfg.julia_version
        )

    def _get_plugins(
        self,
        enabled_plugins: Optional[List[str]],
        license_type: Optional[str],
        plugin_options: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Assemble Julia plugin configuration based on explicitly enabled plugins"""
        plugins = []

        # Map each plugin type to its configuration builder function
        plugin_builders = {
            # Core plugins
            "ProjectFile": lambda: self._build_project_file_plugin(plugin_options),
            "License": lambda: self._build_license_plugin(license_type, plugin_options),
            "Git": lambda: self._build_git_plugin(plugin_options),
            "Formatter": lambda: self._build_formatter_plugin(plugin_options),
            "Tests": lambda: self._build_tests_plugin(plugin_options),
            "SrcDir": lambda: self._build_srcdir_plugin(plugin_options),
            "Readme": lambda: self._build_readme_plugin(plugin_options),
            # CI/CD plugins
            "GitHubActions": lambda: self._build_github_actions_plugin(plugin_options),
            "AppVeyor": lambda: self._build_appveyor_plugin(plugin_options),
            "CirrusCI": lambda: self._build_cirrusci_plugin(plugin_options),
            "DroneCI": lambda: self._build_droneci_plugin(plugin_options),
            "GitLabCI": lambda: self._build_gitlabci_plugin(plugin_options),
            "TravisCI": lambda: self._build_travisci_plugin(plugin_options),
            # Code coverage plugins
            "Codecov": lambda: self._build_codecov_plugin(plugin_options),
            "Coveralls": lambda: self._build_coveralls_plugin(plugin_options),
            # Documentation plugins
            "Documenter": lambda: self._build_documenter_plugin(plugin_options),
            # Automation plugins
            "TagBot": lambda: self._build_tagbot_plugin(plugin_options),
            "CompatHelper": lambda: self._build_compathelper_plugin(plugin_options),
            "Dependabot": lambda: self._build_dependabot_plugin(plugin_options),
            # Badge plugins
            "BlueStyleBadge": lambda: self._build_bluestylebadge_plugin(plugin_options),
            "ColPracBadge": lambda: self._build_colpracbadge_plugin(plugin_options),
            "PkgEvalBadge": lambda: self._build_pkgevalbadge_plugin(plugin_options),
            # Miscellaneous plugins
            "Develop": lambda: self._build_develop_plugin(plugin_options),
            "Citation": lambda: self._build_citation_plugin(plugin_options),
            "RegisterAction": lambda: self._build_registeraction_plugin(plugin_options),
            "CodeOwners": lambda: self._build_codeowners_plugin(plugin_options),
            "PkgBenchmark": lambda: self._build_pkgbenchmark_plugin(plugin_options),
            "Runic": lambda: self._build_runic_plugin(plugin_options),
        }

        # Auto-enable License plugin when license_type is specified or License plugin options exist
        plugins_to_process = list(enabled_plugins or [])
        has_license_options = plugin_options and "License" in plugin_options
        if (
            license_type or has_license_options
        ) and "License" not in plugins_to_process:
            plugins_to_process.append("License")

        for plugin_name in plugins_to_process:
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
        """Create License plugin with full support for all License plugin parameters"""
        license_options = {}

        # Handle legacy license_type parameter
        if license_type:
            mapped_license = self._map_license(license_type)
            license_options["name"] = mapped_license

        # Apply plugin options (takes precedence over legacy license_type)
        if plugin_options and "License" in plugin_options:
            options = plugin_options["License"]
            for key, value in options.items():
                if key == "name":
                    # Apply license mapping to name parameter
                    license_options["name"] = self._map_license(value)
                else:
                    # Pass other parameters through unchanged
                    license_options[key] = value

        # Return None if no license specified
        if not license_options:
            return None

        # Build License plugin with all specified options
        option_strings = []
        for key, value in license_options.items():
            if isinstance(value, str):
                option_strings.append(f'{key}="{value}"')
            else:
                option_strings.append(f"{key}={value}")

        return f"License(; {', '.join(option_strings)})"

    def _build_git_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure Git plugin - uses PkgTemplates.jl defaults unless explicitly overridden"""
        git_options = []

        # Only apply user-specified options
        if plugin_options and "Git" in plugin_options:
            options = plugin_options["Git"]
            if "manifest" in options:
                git_options.append(f"manifest={str(options['manifest']).lower()}")
            if "ssh" in options:
                git_options.append(f"ssh={str(options['ssh']).lower()}")
            if "ignore" in options:
                ignore_patterns = options["ignore"]
                # Support both list and comma-separated string formats from config
                if isinstance(ignore_patterns, list):
                    patterns = [f'"{p}"' for p in ignore_patterns]
                else:
                    patterns = [
                        f'"{p.strip()}"'
                        for p in ignore_patterns.split(",")
                        if p.strip()
                    ]
                git_options.append(f"ignore=[{', '.join(patterns)}]")

        if git_options:
            return f"Git(; {', '.join(git_options)})"
        else:
            return "Git()"

    def _build_formatter_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Build Formatter plugin configuration - uses PkgTemplates.jl defaults unless explicitly overridden"""
        formatter_options = []

        # Only apply user-specified options
        if plugin_options and "Formatter" in plugin_options:
            options = plugin_options["Formatter"]
            if "style" in options:
                formatter_options.append(f'style="{options["style"]}"')

        if formatter_options:
            return f"Formatter(; {', '.join(formatter_options)})"
        else:
            return "Formatter()"

    def _build_tests_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure testing framework - uses PkgTemplates.jl defaults unless explicitly overridden"""
        test_options = []

        # Only apply user-specified options
        if plugin_options and "Tests" in plugin_options:
            options = plugin_options["Tests"]
            if "aqua" in options:
                test_options.append(f"aqua={str(options['aqua']).lower()}")
            if "jet" in options:
                test_options.append(f"jet={str(options['jet']).lower()}")
            if "project" in options:
                test_options.append(f"project={str(options['project']).lower()}")

        if test_options:
            return f"Tests(; {', '.join(test_options)})"
        else:
            return "Tests()"

    def _build_github_actions_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Enable GitHub Actions CI/CD integration for automated testing and deployment"""
        return "GitHubActions()"

    def _build_codecov_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Enable Codecov integration for test coverage reporting"""
        return "Codecov()"

    def _build_documenter_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
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

    # Core documentation plugins
    def _build_srcdir_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure SrcDir plugin - creates src directory structure"""
        return "SrcDir()"

    def _build_readme_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure Readme plugin - generates README.md file"""
        readme_options = []

        if plugin_options and "Readme" in plugin_options:
            options = plugin_options["Readme"]
            if "badge_order" in options:
                badges = options["badge_order"]
                if isinstance(badges, list):
                    badge_list = [f'"{b}"' for b in badges]
                else:
                    badge_list = [
                        f'"{b.strip()}"' for b in badges.split(",") if b.strip()
                    ]
                readme_options.append(f"badge_order=[{', '.join(badge_list)}]")

        if readme_options:
            return f"Readme(; {', '.join(readme_options)})"
        else:
            return "Readme()"

    # CI/CD plugins
    def _build_appveyor_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure AppVeyor CI for Windows testing"""
        appveyor_options = []

        if plugin_options and "AppVeyor" in plugin_options:
            options = plugin_options["AppVeyor"]
            if "config_file" in options:
                appveyor_options.append(f'config_file="{options["config_file"]}"')
            if "coverage" in options:
                appveyor_options.append(f"coverage={str(options['coverage']).lower()}")

        if appveyor_options:
            return f"AppVeyor(; {', '.join(appveyor_options)})"
        else:
            return "AppVeyor()"

    def _build_cirrusci_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure Cirrus CI for testing"""
        cirrus_options = []

        if plugin_options and "CirrusCI" in plugin_options:
            options = plugin_options["CirrusCI"]
            if "config_file" in options:
                cirrus_options.append(f'config_file="{options["config_file"]}"')
            if "coverage" in options:
                cirrus_options.append(f"coverage={str(options['coverage']).lower()}")
            if "image" in options:
                cirrus_options.append(f'image="{options["image"]}"')

        if cirrus_options:
            return f"CirrusCI(; {', '.join(cirrus_options)})"
        else:
            return "CirrusCI()"

    def _build_droneci_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure Drone CI for testing"""
        drone_options = []

        if plugin_options and "DroneCI" in plugin_options:
            options = plugin_options["DroneCI"]
            if "config_file" in options:
                drone_options.append(f'config_file="{options["config_file"]}"')
            if "coverage" in options:
                drone_options.append(f"coverage={str(options['coverage']).lower()}")

        if drone_options:
            return f"DroneCI(; {', '.join(drone_options)})"
        else:
            return "DroneCI()"

    def _build_gitlabci_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure GitLab CI for testing"""
        gitlab_options = []

        if plugin_options and "GitLabCI" in plugin_options:
            options = plugin_options["GitLabCI"]
            if "config_file" in options:
                gitlab_options.append(f'config_file="{options["config_file"]}"')
            if "coverage" in options:
                gitlab_options.append(f"coverage={str(options['coverage']).lower()}")

        if gitlab_options:
            return f"GitLabCI(; {', '.join(gitlab_options)})"
        else:
            return "GitLabCI()"

    def _build_travisci_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure Travis CI for testing"""
        travis_options = []

        if plugin_options and "TravisCI" in plugin_options:
            options = plugin_options["TravisCI"]
            if "config_file" in options:
                travis_options.append(f'config_file="{options["config_file"]}"')
            if "coverage" in options:
                travis_options.append(f"coverage={str(options['coverage']).lower()}")

        if travis_options:
            return f"TravisCI(; {', '.join(travis_options)})"
        else:
            return "TravisCI()"

    # Code coverage plugins
    def _build_coveralls_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure Coveralls for code coverage reporting"""
        coveralls_options = []

        if plugin_options and "Coveralls" in plugin_options:
            options = plugin_options["Coveralls"]
            if "config_file" in options:
                coveralls_options.append(f'config_file="{options["config_file"]}"')

        if coveralls_options:
            return f"Coveralls(; {', '.join(coveralls_options)})"
        else:
            return "Coveralls()"

    # Automation plugins

    def _build_dependabot_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure Dependabot for automated dependency updates"""
        dependabot_options = []

        if plugin_options and "Dependabot" in plugin_options:
            options = plugin_options["Dependabot"]
            if "config_file" in options:
                dependabot_options.append(f'config_file="{options["config_file"]}"')

        if dependabot_options:
            return f"Dependabot(; {', '.join(dependabot_options)})"
        else:
            return "Dependabot()"

    # Badge plugins
    def _build_bluestylebadge_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure BlueStyleBadge for Julia code style"""
        return "BlueStyleBadge()"

    def _build_colpracbadge_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure ColPracBadge for community practices"""
        return "ColPracBadge()"

    def _build_pkgevalbadge_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure PkgEvalBadge for package evaluation"""
        return "PkgEvalBadge()"

    # Miscellaneous plugins
    def _build_develop_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure Develop plugin for development mode setup"""
        return "Develop()"

    def _build_citation_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure Citation plugin for CITATION.bib generation"""
        citation_options = []

        if plugin_options and "Citation" in plugin_options:
            options = plugin_options["Citation"]
            if "file" in options:
                citation_options.append(f'file="{options["file"]}"')

        if citation_options:
            return f"Citation(; {', '.join(citation_options)})"
        else:
            return "Citation()"

    def _build_registeraction_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure RegisterAction plugin for automated package registration"""
        return "RegisterAction()"

    def _build_codeowners_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure CodeOwners plugin for GitHub code ownership"""
        codeowners_options = []

        if plugin_options and "CodeOwners" in plugin_options:
            options = plugin_options["CodeOwners"]
            if "file" in options:
                codeowners_options.append(f'file="{options["file"]}"')

        if codeowners_options:
            return f"CodeOwners(; {', '.join(codeowners_options)})"
        else:
            return "CodeOwners()"

    def _build_pkgbenchmark_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure PkgBenchmark plugin for performance benchmarking"""
        return "PkgBenchmark()"

    def _build_runic_plugin(
        self, plugin_options: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """Configure Runic plugin for Julia code formatting"""
        runic_options = []

        if plugin_options and "Runic" in plugin_options:
            options = plugin_options["Runic"]
            for key, value in options.items():
                if isinstance(value, str):
                    runic_options.append(f'{key}="{value}"')
                else:
                    runic_options.append(f"{key}={str(value).lower()}")

        if runic_options:
            return f"Runic(; {', '.join(runic_options)})"
        else:
            return "Runic()"

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
        """Generate Julia Template function code for visualization using Jinja2 template"""
        # Generate Julia code using the same Jinja2 template
        template = self.jinja_env.get_template("julia_template.j2")
        julia_code = template.render(
            package_name=package_name,
            author=author,
            user=user,
            mail=mail,
            output_dir=str(output_dir),
            plugins=plugins["plugins"],
            julia_version=julia_version,
        )

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
        """Execute PkgTemplates.jl package generation via Jinja2 template"""
        # Generate Julia code using Jinja2 template
        template = self.jinja_env.get_template("julia_template.j2")
        julia_code = template.render(
            package_name=package_name,
            author=author,
            user=user,
            mail=mail,
            output_dir=str(output_dir),
            plugins=plugins["plugins"],
            julia_version=julia_version,
        )

        cmd = ["julia", "-e", julia_code]

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
                        f"Julia execution failed with exit code {e.returncode}"
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
                        error_msg = f"Julia execution failed: {e.stdout}"
                    # Only show PkgTemplates installation hint for actual module loading errors
                    if (
                        "ArgumentError: Package PkgTemplates not found" in e.stderr
                        or "LoadError" in e.stderr
                        and "PkgTemplates" in e.stderr
                    ):
                        error_msg += "\nHint: Make sure PkgTemplates.jl is installed: julia -e 'using Pkg; Pkg.add(\"PkgTemplates\")'"
                    raise RuntimeError(error_msg) from e
                else:
                    # Handle case where Julia generates warnings but completes successfully
                    package_dir = output_dir / package_name
                    if package_dir.exists():
                        return package_dir
                    else:
                        error_msg = f"Julia execution failed: {e.stderr}"
                        raise RuntimeError(error_msg) from e
        except FileNotFoundError:
            raise RuntimeError(
                "Julia not found. Please install Julia and ensure it's in your PATH."
            )

    def _add_mise_config(
        self, package_dir: Path, package_name: str, mise_filename_base: str = ".mise"
    ) -> None:
        """Add mise configuration to the package"""
        template = self.jinja_env.get_template("mise.toml.j2")

        mise_content = template.render(
            package_name=package_name,
            project_dir=".",
            mise_config_basename=mise_filename_base,
        )

        mise_file = package_dir / f"{mise_filename_base}.toml"
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
