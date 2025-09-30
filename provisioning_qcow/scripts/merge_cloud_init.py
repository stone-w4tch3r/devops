#!/usr/bin/env python3
"""
Cloud-init Configuration Merger

This script merges multiple cloud-init YAML files into a single configuration file.
It processes a master file with #include directives and merges the referenced files.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any, Union


def merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries with special handling for cloud-init arrays.
    
    Cloud-init arrays (like runcmd, write_files) should be concatenated, not replaced.
    """
    result = base.copy()
    
    for key, value in update.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                result[key] = merge_dicts(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                # Concatenate lists (important for cloud-init arrays like runcmd, write_files)
                result[key] = result[key] + value
            else:
                # Replace value (for scalars and mixed types)
                result[key] = value
        else:
            result[key] = value
    
    return result


def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file, handling cloud-config headers."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove #cloud-config header if present
        lines = content.split('\n')
        if lines and lines[0].strip() == '#cloud-config':
            content = '\n'.join(lines[1:])
        
        # Parse YAML
        data = yaml.safe_load(content) or {}
        
        # Ensure we have a dictionary
        if not isinstance(data, dict):
            print(f"Warning: {file_path} does not contain a YAML dictionary, skipping")
            return {}
        
        return data
        
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse YAML in {file_path}: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to read {file_path}: {e}")
        sys.exit(1)


def process_includes(master_file: Path, base_dir: Path) -> List[Path]:
    """
    Parse the master file and extract include file paths.
    
    Supports both:
    - #include followed by a list of files
    - Direct YAML with includes in the content
    """
    try:
        with open(master_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        include_files = []
        
        # Look for #include directive
        in_include_section = False
        for line in lines:
            line = line.strip()
            
            if line == '#include':
                in_include_section = True
                continue
            
            if in_include_section:
                if line.startswith('#') and line != '#cloud-config':
                    # End of include section (next directive)
                    break
                elif line.startswith('-'):
                    # YAML list item
                    file_path = line[1:].strip()
                    if file_path:
                        # Handle relative paths
                        if file_path.startswith('./'):
                            file_path = file_path[2:]
                        include_files.append(base_dir / file_path)
                elif line == '' or line.startswith('#cloud-config'):
                    # Empty line or start of actual config
                    continue
                else:
                    # End of include section
                    break
        
        # If no includes found via #include directive, try parsing as YAML
        if not include_files:
            try:
                data = yaml.safe_load(content)
                if isinstance(data, list):
                    # Direct list of files
                    for item in data:
                        if isinstance(item, str):
                            if item.startswith('./'):
                                item = item[2:]
                            include_files.append(base_dir / item)
            except yaml.YAMLError:
                pass  # Not valid YAML, that's okay
        
        return include_files
        
    except Exception as e:
        print(f"Error: Failed to process includes from {master_file}: {e}")
        sys.exit(1)


def merge_cloud_init_configs(master_file: Path, output_file: Path) -> None:
    """Main function to merge cloud-init configurations."""
    
    # Validate master file exists
    if not master_file.exists():
        print(f"Error: Master file not found: {master_file}")
        sys.exit(1)
    
    base_dir = master_file.parent
    print(f"📋 Processing master file: {master_file}")
    print(f"📁 Base directory: {base_dir}")
    
    # Get list of files to include
    include_files = process_includes(master_file, base_dir)
    
    if not include_files:
        print("Warning: No include files found in master file")
        # Copy master file as-is if it contains actual config
        try:
            with open(master_file, 'r') as f:
                content = f.read()
            # If it's not just includes, copy it
            if not content.strip().startswith('#include'):
                with open(output_file, 'w') as f:
                    f.write(content)
                print(f"✅ Copied master file to: {output_file}")
                return
        except Exception as e:
            print(f"Error: Failed to copy master file: {e}")
            sys.exit(1)
    
    print(f"📦 Found {len(include_files)} files to merge:")
    for f in include_files:
        print(f"   - {f}")
    
    # Start with empty config
    merged_config = {}
    
    # Process each include file
    for include_file in include_files:
        if not include_file.exists():
            print(f"Warning: Include file not found: {include_file}, skipping")
            continue
        
        print(f"🔄 Processing: {include_file}")
        file_config = load_yaml_file(include_file)
        
        if file_config:
            merged_config = merge_dicts(merged_config, file_config)
            print(f"✅ Merged: {include_file} ({len(file_config)} top-level keys)")
        else:
            print(f"⚠️  Skipped: {include_file} (empty or invalid)")
    
    # Write merged configuration
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("#cloud-config\n")
            f.write("# Merged cloud-init configuration\n")
            f.write(f"# Generated from: {master_file}\n\n")
            
            yaml.dump(merged_config, f, 
                     default_flow_style=False, 
                     sort_keys=False,
                     indent=2,
                     width=120)
        
        print(f"\n🎯 Successfully merged configuration:")
        print(f"   📝 Output file: {output_file}")
        print(f"   🔑 Total keys: {len(merged_config)}")
        print(f"   📊 Keys: {list(merged_config.keys())}")
        
    except Exception as e:
        print(f"Error: Failed to write output file: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Merge cloud-init configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s cloud-init-golden/user-data-master.yml .runtime/user-data-merged.yml
  %(prog)s -i cloud-init-golden/user-data-master.yml -o .runtime/user-data.yml
        """
    )
    
    parser.add_argument('master_file', nargs='?',
                       help='Master cloud-init file with #include directives')
    parser.add_argument('output_file', nargs='?',
                       help='Output file for merged configuration')
    parser.add_argument('-i', '--input', dest='master_file_alt',
                       help='Master cloud-init file (alternative to positional arg)')
    parser.add_argument('-o', '--output', dest='output_file_alt',
                       help='Output file (alternative to positional arg)')
    parser.add_argument('--validate', action='store_true',
                       help='Validate output file after merging')
    
    args = parser.parse_args()
    
    # Determine input and output files
    master_file = args.master_file or args.master_file_alt
    output_file = args.output_file or args.output_file_alt
    
    if not master_file:
        parser.error("Master file is required (use positional argument or -i/--input)")
    if not output_file:
        parser.error("Output file is required (use positional argument or -o/--output)")
    
    master_file = Path(master_file)
    output_file = Path(output_file)
    
    print("🔧 Cloud-init Configuration Merger")
    print("=" * 40)
    
    merge_cloud_init_configs(master_file, output_file)
    
    if args.validate:
        print("\n🔍 Validating merged configuration...")
        # Import and run validator (will be implemented)
        try:
            from validate_cloud_init import validate_config
            is_valid = validate_config(output_file)
            if is_valid:
                print("✅ Configuration validation passed")
            else:
                print("❌ Configuration validation failed")
                sys.exit(1)
        except ImportError:
            print("⚠️  Validator not available, skipping validation")


if __name__ == "__main__":
    main()