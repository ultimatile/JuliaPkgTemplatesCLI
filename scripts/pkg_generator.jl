#!/usr/bin/env julia

"""
Julia script to generate packages using PkgTemplates.jl
Called from Python jugen CLI tool
"""

using Pkg
using PkgTemplates

function parse_plugins(plugins_str::String)
    """Parse plugins string from Python and return Julia array"""
    # Remove brackets and split by comma
    plugins_str = strip(plugins_str, ['[', ']'])
    plugin_strs = split(plugins_str, ',')
    
    plugins = []
    for plugin_str in plugin_strs
        plugin_str = strip(plugin_str)
        if isempty(plugin_str)
            continue
        end
        
        # Parse different plugin types
        if occursin("License", plugin_str)
            # Extract license name: License(; name="MIT")
            license_match = match(r"License\(;\s*name=\"(\w+)\"\)", plugin_str)
            if license_match !== nothing
                license_name = license_match.captures[1]
                if license_name == "MIT"
                    push!(plugins, License(; name="MIT"))
                elseif license_name == "Apache-2.0"
                    push!(plugins, License(; name="Apache-2.0"))
                elseif license_name == "BSD-3-Clause"
                    push!(plugins, License(; name="BSD-3-Clause"))
                elseif license_name == "GPL-3.0"
                    push!(plugins, License(; name="GPL-3.0"))
                else
                    push!(plugins, License(; name="MIT"))  # Default fallback
                end
            else
                push!(plugins, License(; name="MIT"))  # Default fallback
            end
        elseif occursin("Git", plugin_str) && occursin("manifest=true", plugin_str)
            push!(plugins, Git(; manifest=true))
        elseif occursin("GitHubActions()", plugin_str)
            push!(plugins, GitHubActions())
        elseif occursin("Codecov()", plugin_str)
            push!(plugins, Codecov())
        elseif occursin("Documenter{GitHubActions}()", plugin_str)
            push!(plugins, Documenter{GitHubActions}())
        elseif occursin("Develop()", plugin_str)
            push!(plugins, Develop())
        elseif occursin("TagBot()", plugin_str)
            push!(plugins, TagBot())
        elseif occursin("CompatHelper()", plugin_str)
            push!(plugins, CompatHelper())
        else
            @warn "Unknown plugin: $plugin_str"
        end
    end
    
    return plugins
end

function generate_package(package_name::String, author::String, output_dir::String, plugins_str::String)
    """Generate Julia package using PkgTemplates.jl"""
    
    # Validate package name
    if !occursin(r"^[A-Za-z][A-Za-z0-9_]*$", package_name)
        error("Invalid package name: $package_name. Package names must start with a letter and contain only letters, numbers, and underscores.")
    end
    
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
        println("✅ Package created successfully at: $package_dir")
        return package_dir
    catch e
        println("❌ Error creating package: $e")
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
