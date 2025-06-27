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

try
    using LibGit2: GitError
catch
    GitError = Exception
end


function parse_plugins(plugins_str::String)
  """Parse plugins string from Python and return Julia array"""
  plugin_patterns = Dict(
    r"GitHubActions\(\)" => () -> GitHubActions(),
    r"Codecov\(\)" => () -> Codecov(),
    r"Documenter\{GitHubActions\}\(\)" => () -> Documenter{GitHubActions}(),
    r"Develop\(\)" => () -> Develop(),
    r"TagBot\(\)" => () -> TagBot(),
    r"CompatHelper\(\)" => () -> CompatHelper()
  )

  plugins_str = strip(plugins_str, ['[', ']'])
  plugin_strs = split(plugins_str, ',')

  plugins = []
  for plugin_str in plugin_strs
    plugin_str = strip(plugin_str)
    if isempty(plugin_str)
      continue
    end

    if occursin("License", plugin_str)
      license_match = match(r"License\(;\s*name=\"([^\"]+)\"\)", plugin_str)
      if license_match !== nothing
        license_name = license_match.captures[1]
        push!(plugins, License(; name=license_name))
      else
        push!(plugins, License(; name="MIT"))
      end
      continue
    end

    if occursin("Formatter", plugin_str)
      formatter_match = match(r"Formatter\(;\s*style=\"(\w+)\"\)", plugin_str)
      if formatter_match !== nothing
        style = formatter_match.captures[1]
        push!(plugins, Formatter(; style=style))
      else
        push!(plugins, Formatter())
      end
      continue
    end

    if occursin("Git", plugin_str)
      git_params = Dict{Symbol, Any}()
      
      if occursin("manifest=true", plugin_str)
        git_params[:manifest] = true
      end
      
      if occursin("ssh=true", plugin_str)
        git_params[:ssh] = true
      end
      
      ignore_match = match(r"ignore=\[([^\]]+)\]", plugin_str)
      if ignore_match !== nothing
        ignore_str = ignore_match.captures[1]
        patterns = [strip(s, ['"', ' ']) for s in split(ignore_str, ',') if !isempty(strip(s))]
        git_params[:ignore] = patterns
      end
      
      push!(plugins, Git(; git_params...))
      continue
    end

    if occursin("Tests", plugin_str)
      test_params = Dict{Symbol, Any}()
      
      if occursin("project=true", plugin_str)
        test_params[:project] = true
      end
      
      if occursin("aqua=true", plugin_str)
        test_params[:aqua] = true
      end
      
      if occursin("jet=true", plugin_str)
        test_params[:jet] = true
      end
      
      push!(plugins, Tests(; test_params...))
      continue
    end

    if occursin("ProjectFile", plugin_str)
      version_match = match(r"ProjectFile\(;\s*version=v\"([^\"]+)\"\)", plugin_str)
      if version_match !== nothing
        version_str = version_match.captures[1]
        push!(plugins, ProjectFile(; version=VersionNumber(version_str)))
      else
        push!(plugins, ProjectFile())
      end
      continue
    end

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

function generate_package(package_name::String, author::String, user::String, output_dir::String, plugins_str::String, julia_version::Union{String, Nothing}=nothing)
  """Generate Julia package using PkgTemplates.jl"""

  plugins = parse_plugins(plugins_str)

  println("Creating package: $package_name")
  println("Author: $author")
  println("User: $user")
  println("Output directory: $output_dir")
  println("Plugins: $(length(plugins)) plugins configured")
  if julia_version !== nothing
    println("Julia version: $julia_version")
  end

  template_args = Dict(:dir => output_dir, :plugins => plugins)
  
  # Add author parameter if provided
  if !isempty(author)
    template_args[:authors] = [author]
  end
  
  # Add user parameter if provided (otherwise PkgTemplates.jl uses git config)
  if !isempty(user)
    template_args[:user] = user
  end
  
  if julia_version !== nothing
    version_str = replace(julia_version, "v" => "")
    template_args[:julia] = VersionNumber(version_str)
  end
  
  template = Template(; template_args...)

  try
    package_dir = template(package_name)
    println("Package created successfully at: $package_dir")
    return package_dir
  catch e
    println("Error creating package: $e")
    if isa(e, GitError)
      println("Git error details: $(e.msg)")
      println("Git error code: $(e.code)")
      println("Git error class: $(e.class)")
    end
    rethrow(e)
  end
end

function main()
  if length(ARGS) < 5
    println("Usage: julia pkg_generator.jl <package_name> <author> <user> <output_dir> <plugins> [julia_version]")
    println("Example: julia pkg_generator.jl MyPackage \"John Doe\" \"johndoe\" \"/path/to/output\" \"[License(; name=\\\"MIT\\\"), Git(; manifest=true)]\" \"v1.10.9\"")
    exit(1)
  end

  package_name = ARGS[1]
  author = ARGS[2]
  user = ARGS[3]
  output_dir = ARGS[4]
  plugins_str = ARGS[5]
  julia_version = length(ARGS) >= 6 ? ARGS[6] : nothing

  try
    generate_package(package_name, author, user, output_dir, plugins_str, julia_version)
  catch e
    println("Error: $e")
    exit(1)
  end
end

if abspath(PROGRAM_FILE) == @__FILE__
  main()
end
