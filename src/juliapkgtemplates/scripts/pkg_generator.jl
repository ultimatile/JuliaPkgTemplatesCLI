#!/usr/bin/env julia

"""
Julia script to generate packages using PkgTemplates.jl
Called from Python jugen CLI tool
"""

using Pkg

println("Loading PkgTemplates.jl...")
try
    using PkgTemplates
    println("PkgTemplates.jl loaded successfully")
catch e
    println("Error loading PkgTemplates.jl: ", e)
    rethrow(e)
end


function parse_plugins(plugins_str::String)
  """Parse plugins string from Python and return Julia array"""
  # Plugin mapping table
  plugin_patterns = Dict(
    r"Git.*manifest=true" => () -> Git(; manifest=true),
    r"GitHubActions\(\)" => () -> GitHubActions(),
    r"Codecov\(\)" => () -> Codecov(),
    r"Documenter\{GitHubActions\}\(\)" => () -> Documenter{GitHubActions}(),
    r"Develop\(\)" => () -> Develop(),
    r"TagBot\(\)" => () -> TagBot(),
    r"CompatHelper\(\)" => () -> CompatHelper()
  )

  # Remove brackets and split by comma
  plugins_str = strip(plugins_str, ['[', ']'])
  plugin_strs = split(plugins_str, ',')

  plugins = []
  for plugin_str in plugin_strs
    plugin_str = strip(plugin_str)
    if isempty(plugin_str)
      continue
    end

    # Handle License plugin specially (requires parameter extraction)
    if occursin("License", plugin_str)
      license_match = match(r"License\(;\s*name=\"([^\"]+)\"\)", plugin_str)
      if license_match !== nothing
        license_name = license_match.captures[1]
        push!(plugins, License(; name=license_name))
      else
        push!(plugins, License(; name="MIT"))  # Default fallback
      end
      continue
    end

    # Handle Formatter plugin specially (requires parameter extraction)
    if occursin("Formatter", plugin_str)
      formatter_match = match(r"Formatter\(;\s*style=\"(\w+)\"\)", plugin_str)
      if formatter_match !== nothing
        style = formatter_match.captures[1]
        push!(plugins, Formatter(; style=style))
      else
        push!(plugins, Formatter())  # Default nostyle
      end
      continue
    end

    # Check against plugin patterns table
    matched = false
    for (pattern, creator) in plugin_patterns
      if occursin(pattern, plugin_str)
        push!(plugins, creator())
        matched = true
        break
      end
    end

    if !matched
      @warn "Unknown plugin: $plugin_str"
    end
  end

  return plugins
end

function generate_package(package_name::String, author::String, output_dir::String, plugins_str::String)
  """Generate Julia package using PkgTemplates.jl"""

  # Parse plugins
  plugins = parse_plugins(plugins_str)

  println("Creating package: $package_name")
  println("Author: $author")
  println("Output directory: $output_dir")
  println("Plugins: $(length(plugins)) plugins configured")

  # Create template
  template = Template(;
    user=author,
    dir=output_dir,
    plugins=plugins
  )

  # Generate package
  try
    package_dir = template(package_name)
    println("Package created successfully at: $package_dir")
    return package_dir
  catch e
    println("Error creating package: $e")
    rethrow(e)
  end
end

function main()
  if length(ARGS) < 4
    println("Usage: julia pkg_generator.jl <package_name> <author> <output_dir> <plugins>")
    println("Example: julia pkg_generator.jl MyPackage \"John Doe\" \"/path/to/output\" \"[License(; name=\\\"MIT\\\"), Git(; manifest=true)]\"")
    exit(1)
  end

  package_name = ARGS[1]
  author = ARGS[2]
  output_dir = ARGS[3]
  plugins_str = ARGS[4]

  try
    generate_package(package_name, author, output_dir, plugins_str)
  catch e
    println("Error: $e")
    exit(1)
  end
end

# Run if called directly
if abspath(PROGRAM_FILE) == @__FILE__
  main()
end
