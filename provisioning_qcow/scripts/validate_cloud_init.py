#!/usr/bin/env python3
"""
Cloud-init Configuration Validator

This script validates cloud-init configuration files for syntax and schema compliance.
Currently a mock implementation that returns true - will be enhanced with actual validation.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional


def validate_yaml_syntax(file_path: Path) -> bool:
    """
    Validate YAML syntax of the configuration file.
    
    Returns:
        bool: True if valid YAML syntax, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove #cloud-config header for YAML parsing
        lines = content.split('\n')
        if lines and lines[0].strip() == '#cloud-config':
            content = '\n'.join(lines[1:])
        
        # Parse YAML
        data = yaml.safe_load(content)
        
        # Check if it's a valid dictionary (cloud-config should be)
        if not isinstance(data, dict):
            print(f"❌ Error: Configuration is not a valid YAML dictionary")
            return False
        
        print(f"✅ YAML syntax validation passed")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False


def validate_cloud_config_header(file_path: Path) -> bool:
    """
    Validate that the file has the proper #cloud-config header.
    
    Returns:
        bool: True if header is present, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        
        if first_line == '#cloud-config':
            print(f"✅ Cloud-config header validation passed")
            return True
        else:
            print(f"❌ Missing or invalid #cloud-config header: '{first_line}'")
            return False
            
    except Exception as e:
        print(f"❌ Error checking header: {e}")
        return False


def validate_required_sections(config_data: Dict[str, Any]) -> bool:
    """
    Validate that required sections are present in the configuration.
    
    Args:
        config_data: Parsed cloud-init configuration
        
    Returns:
        bool: True if required sections are present, False otherwise
    """
    # Define recommended sections for a golden VM template
    recommended_sections = {
        'users': 'User account configuration',
        'package_update': 'Package update configuration', 
        'package_upgrade': 'Package upgrade configuration'
    }
    
    # Define critical sections that should be present
    critical_sections = ['users']
    
    missing_critical = []
    missing_recommended = []
    
    for section in critical_sections:
        if section not in config_data:
            missing_critical.append(section)
    
    for section in recommended_sections:
        if section not in config_data:
            missing_recommended.append(section)
    
    # Report results
    if missing_critical:
        print(f"❌ Missing critical sections: {missing_critical}")
        return False
    
    if missing_recommended:
        print(f"⚠️  Missing recommended sections: {missing_recommended}")
        # Not a failure, but worth noting
    
    print(f"✅ Section validation passed")
    return True


def validate_user_configuration(config_data: Dict[str, Any]) -> bool:
    """
    Validate user configuration for common issues.
    
    Args:
        config_data: Parsed cloud-init configuration
        
    Returns:
        bool: True if user config is valid, False otherwise
    """
    if 'users' not in config_data:
        return True  # Already checked in required sections
    
    users = config_data['users']
    if not isinstance(users, list):
        print(f"❌ 'users' should be a list, got {type(users)}")
        return False
    
    for i, user in enumerate(users):
        if not isinstance(user, dict):
            print(f"❌ User {i} should be a dictionary, got {type(user)}")
            return False
        
        # Check for common user config issues
        if 'name' not in user:
            print(f"❌ User {i} is missing required 'name' field")
            return False
        
        # Check for deprecated password fields (our previous bug)
        deprecated_fields = ['passwd', 'plain_text_passwd']
        for field in deprecated_fields:
            if field in user:
                print(f"❌ User '{user['name']}' uses deprecated field '{field}' - use chpasswd module instead")
                return False
    
    print(f"✅ User configuration validation passed")
    return True


def mock_schema_validation() -> bool:
    """
    Mock schema validation - always returns True for now.
    
    TODO: Implement actual cloud-init schema validation using:
    - Cloud-init's built-in schema validation
    - JSONSchema validation against cloud-init schema
    - Custom validation rules
    
    Returns:
        bool: Always True (mock implementation)
    """
    print(f"✅ Schema validation passed (mock - always returns True)")
    return True


def validate_config(file_path: Path, verbose: bool = False) -> bool:
    """
    Main validation function that runs all validation checks.
    
    Args:
        file_path: Path to the cloud-init configuration file
        verbose: Enable verbose output
        
    Returns:
        bool: True if all validations pass, False otherwise
    """
    if verbose:
        print(f"🔍 Validating cloud-init configuration: {file_path}")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    # Run validation checks
    checks = [
        ("YAML Syntax", lambda: validate_yaml_syntax(file_path)),
        ("Cloud-config Header", lambda: validate_cloud_config_header(file_path)),
    ]
    
    # Parse config for further validation
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        if lines and lines[0].strip() == '#cloud-config':
            content = '\n'.join(lines[1:])
        
        config_data = yaml.safe_load(content) or {}
        
        # Add config-dependent checks
        checks.extend([
            ("Required Sections", lambda: validate_required_sections(config_data)),
            ("User Configuration", lambda: validate_user_configuration(config_data)),
            ("Schema Validation", lambda: mock_schema_validation()),
        ])
        
    except Exception as e:
        print(f"❌ Failed to parse config for detailed validation: {e}")
        return False
    
    # Run all checks
    all_passed = True
    for check_name, check_func in checks:
        if verbose:
            print(f"\n🔸 Running {check_name}...")
        
        try:
            result = check_func()
            if not result:
                all_passed = False
                if verbose:
                    print(f"  ❌ {check_name} failed")
            elif verbose:
                print(f"  ✅ {check_name} passed")
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate cloud-init configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s .runtime/user-data-merged.yml
  %(prog)s --verbose cloud-init-golden/00-base.yml
  %(prog)s --all-files cloud-init-golden/
        """
    )
    
    parser.add_argument('config_file', nargs='?',
                       help='Cloud-init configuration file to validate')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--all-files', metavar='DIRECTORY',
                       help='Validate all .yml files in specified directory')
    
    args = parser.parse_args()
    
    if args.all_files:
        # Validate all yml files in directory
        directory = Path(args.all_files)
        if not directory.exists() or not directory.is_dir():
            print(f"Error: Directory not found: {directory}")
            sys.exit(1)
        
        yml_files = list(directory.glob('*.yml'))
        if not yml_files:
            print(f"No .yml files found in {directory}")
            sys.exit(1)
        
        print(f"🔍 Validating {len(yml_files)} files in {directory}")
        print("=" * 50)
        
        all_valid = True
        for yml_file in sorted(yml_files):
            print(f"\n📄 Validating: {yml_file.name}")
            print("-" * 30)
            is_valid = validate_config(yml_file, args.verbose)
            if not is_valid:
                all_valid = False
        
        print(f"\n{'✅ All files valid!' if all_valid else '❌ Some files have validation errors'}")
        sys.exit(0 if all_valid else 1)
    
    elif args.config_file:
        config_file = Path(args.config_file)
        print("🔍 Cloud-init Configuration Validator")
        print("=" * 40)
        
        is_valid = validate_config(config_file, args.verbose)
        
        print(f"\n{'✅ Configuration is valid!' if is_valid else '❌ Configuration has validation errors'}")
        sys.exit(0 if is_valid else 1)
    
    else:
        parser.error("Either config_file or --all-files must be specified")


if __name__ == "__main__":
    main()