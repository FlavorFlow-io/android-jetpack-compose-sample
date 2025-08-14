#!/usr/bin/env python3
"""
FlavorFlow Branding Application Script

This script applies branding configuration to an Android project based on
the flavor configuration JSON file.
"""

import json
import os
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw

# Constants
JAVA_SOURCE_DIR = 'src/main/java'
KOTLIN_SOURCE_DIR = 'src/main/kotlin'
TEST_JAVA_SOURCE_DIR = 'src/test/java'
TEST_KOTLIN_SOURCE_DIR = 'src/test/kotlin'
ANDROID_TEST_JAVA_SOURCE_DIR = 'src/androidTest/java'
ANDROID_TEST_KOTLIN_SOURCE_DIR = 'src/androidTest/kotlin'

# File extensions
JAVA_EXTENSION = '.java'
KOTLIN_EXTENSION = '.kt'
SOURCE_EXTENSIONS = [JAVA_EXTENSION, KOTLIN_EXTENSION]

# Regex patterns
PACKAGE_PATTERN = r'^package\s+([a-zA-Z][a-zA-Z0-9_.]*)'

# Global variable to cache the Android app module path
_android_app_module = None

def find_android_app_module():
    """Find the Android application module by looking for build.gradle with android application plugin"""
    global _android_app_module
    
    # Return cached result if already found
    if _android_app_module is not None:
        return _android_app_module
    
    # Search for build.gradle files in the current directory and subdirectories
    for build_file in Path('.').glob('**/build.gradle*'):
        if build_file.is_file():
            try:
                with open(build_file, 'r') as f:
                    content = f.read()
                
                # Check for Android application plugin in various formats
                if (is_android_application_plugin(content)):
                    app_module_dir = build_file.parent
                    print(f"📱 Found Android app module: {app_module_dir}")
                    _android_app_module = app_module_dir
                    return app_module_dir
                    
            except Exception as e:
                print(f"⚠ Error reading {build_file}: {e}")
                continue
    
    # Fallback to 'app' directory if nothing found
    print("⚠ No Android app module found, falling back to 'app' directory")
    _android_app_module = Path('app')
    return _android_app_module

def has_android_application_plugin(content):
    """Check if build.gradle content contains Android application plugin declaration"""
    # Traditional plugin application
    if ('com.android.application' in content or 
        "apply plugin: 'com.android.application'" in content):
        return True
    
    # Kotlin DSL style
    if ("id 'com.android.application'" in content or
        'id("com.android.application")' in content):
        return True
    
    # Version catalog style
    if (re.search(r'alias\s*\(\s*libs\.plugins\.android\.application\s*\)', content) or
        re.search(r'id\s*\(\s*libs\.plugins\.android\.application\s*\)', content)):
        return True
    
    # Version catalog with string interpolation
    if re.search(r'id\s*\(\s*["\'].*android\.application["\']\s*\)', content):
        return True
    
    # Check plugins block
    return has_android_application_in_plugins_block(content)

def has_android_application_in_plugins_block(content):
    """Check for android.application in plugins block"""
    if 'plugins {' not in content:
        return False
        
    plugins_match = re.search(r'plugins\s*\{([^}]+)\}', content, re.DOTALL)
    if not plugins_match:
        return False
        
    plugins_block = plugins_match.group(1)
    
    # Look for android.application in plugins block (but not with "apply false")
    if ('android.application' in plugins_block or
        'libs.plugins.android.application' in plugins_block):
        # Check if it's not applied as false (which would be in root build.gradle)
        return 'apply false' not in plugins_block
    
    return False

def has_android_config_block(content):
    """Check if build.gradle content contains android configuration block"""
    return re.search(r'android\s*\{', content) is not None

def is_android_application_plugin(content):
    """Check if build.gradle content contains Android application plugin and android configuration"""
    return has_android_application_plugin(content) and has_android_config_block(content)

def reset_android_app_module_cache():
    """Reset the cached Android app module path (useful for testing)"""
    global _android_app_module
    _android_app_module = None

def get_app_source_path(subpath=""):
    """Get the path to app sources, dynamically finding the app module"""
    app_module = find_android_app_module()
    if subpath:
        return app_module / subpath
    return app_module

def load_config(file_path):
    """Load the flavor configuration from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def update_app_name(config):
    """Update app name in strings.xml"""
    strings_path = get_app_source_path('src/main/res/values/strings.xml')
    if strings_path.exists():
        with open(strings_path, 'r') as f:
            content = f.read()
        
        # Replace app_name string resource
        pattern = r'<string name="app_name">[^<]*</string>'
        replacement = f'<string name="app_name">{config["appName"]}</string>'
        content = re.sub(pattern, replacement, content)
        
        with open(strings_path, 'w') as f:
            f.write(content)
        print(f"✓ Updated app name to: {config['appName']}")
    else:
        print("⚠ strings.xml not found, creating basic version")
        os.makedirs(strings_path.parent, exist_ok=True)
        with open(strings_path, 'w') as f:
            f.write(f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{config["appName"]}</string>
</resources>''')

def update_colors(config):
    """Update colors in colors.xml and Compose theme files"""
    # Update XML colors (for compatibility)
    update_xml_colors(config)
    
    # Update Compose theme files
    update_compose_theme(config)

def update_xml_colors(config):
    """Update colors in colors.xml"""
    colors_path = get_app_source_path('src/main/res/values/colors.xml')
    
    # Get colors
    branding = config["branding"]
    primary_color = branding.get("primary", "#6650a4")
    secondary_color = branding.get("secondary", "#625b71")
    background_color = branding.get("background", "#FFFBFE")
    
    # Create colors.xml content
    colors_content = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="primary_color">{primary_color}</color>
    <color name="secondary_color">{secondary_color}</color>
    <color name="background_color">{background_color}</color>
    
    <!-- Material Design Colors -->
    <color name="purple_200">{primary_color}</color>
    <color name="purple_500">{primary_color}</color>
    <color name="purple_700">{secondary_color}</color>
    <color name="teal_200">{secondary_color}</color>
    <color name="teal_700">{secondary_color}</color>
    <color name="black">#FF000000</color>
    <color name="white">#FFFFFFFF</color>
</resources>'''
    
    os.makedirs(colors_path.parent, exist_ok=True)
    with open(colors_path, 'w') as f:
        f.write(colors_content)
    print(f"✓ Updated XML colors: primary={primary_color}, secondary={secondary_color}")

def update_compose_theme(config):
    """Update Compose theme files"""
    # Look for existing Compose theme files using the current package name
    theme_files = find_compose_theme_files(config)
    
    if theme_files:
        for theme_file in theme_files:
            update_existing_compose_theme(theme_file, config)
    else:
        # Create new Compose theme files
        create_compose_theme_files(config)

def find_compose_theme_files(config=None):
    """Find existing Compose theme files"""
    theme_files = []
    app_module = find_android_app_module()  # This will use cached result
    
    # If config is provided, search in the correct package structure
    if config:
        package_path = config["packageName"].replace('.', '/')
        specific_search_paths = [
            f'{JAVA_SOURCE_DIR}/{package_path}/ui/theme',
            f'{KOTLIN_SOURCE_DIR}/{package_path}/ui/theme',
            f'{JAVA_SOURCE_DIR}/{package_path}/theme',
            f'{KOTLIN_SOURCE_DIR}/{package_path}/theme'
        ]
        
        for search_path in specific_search_paths:
            path = app_module / search_path
            if path.exists() and path.is_dir():
                # Look for theme-related files
                for file in path.glob('*.kt'):
                    if any(keyword in file.name.lower() for keyword in ['color', 'theme']):
                        theme_files.append(file)
    
    # Fallback: Common paths for Compose theme files relative to app module
    search_paths = [
        f'{JAVA_SOURCE_DIR}/**/ui/theme',
        f'{KOTLIN_SOURCE_DIR}/**/ui/theme',
        f'{JAVA_SOURCE_DIR}/**/theme',
        f'{KOTLIN_SOURCE_DIR}/**/theme'
    ]
    
    for search_path in search_paths:
        for path in app_module.glob(search_path):
            if path.is_dir():
                # Look for theme-related files
                for file in path.glob('*.kt'):
                    if any(keyword in file.name.lower() for keyword in ['color', 'theme']) and file not in theme_files:
                        theme_files.append(file)
    
    return theme_files

def detect_existing_package_structure(main_source_dir):
    """Detect existing package structure to preserve subdirectories"""
    if not main_source_dir.exists():
        return None
    
    # Look for the first source file and analyze its package structure
    for file_path in main_source_dir.rglob('*.kt'):
        if file_path.is_file():
            package_info = extract_package_info(file_path)
            if package_info:
                return build_package_structure_path(main_source_dir, package_info)
    
    # Fallback: Return the deepest existing directory
    return find_deepest_package_directory(main_source_dir)

def extract_package_info(file_path):
    """Extract package information from a source file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        package_match = re.search(PACKAGE_PATTERN, content, re.MULTILINE)
        if package_match:
            package_name = package_match.group(1)
            package_parts = package_name.split('.')
            return package_parts
            
    except Exception as e:
        print(f"⚠ Error reading {file_path}: {e}")
    
    return None

def build_package_structure_path(main_source_dir, package_parts):
    """Build the filesystem path from package parts"""
    if len(package_parts) > 3:
        # Assume first 3 parts are base package, rest are subdirectories
        base_parts = package_parts[:3]
        subdir_parts = package_parts[3:]
        
        # Build path: main_source_dir/base_package/subdirs
        path = main_source_dir
        for part in base_parts + subdir_parts:
            path = path / part
        return path
    
    return None

def find_deepest_package_directory(main_source_dir):
    """Find the deepest package directory as fallback"""
    deepest_dir = None
    max_depth = 0
    
    for file_path in main_source_dir.rglob('*.kt'):
        if file_path.is_file():
            relative_path = file_path.parent.relative_to(main_source_dir)
            depth = len(relative_path.parts)
            if depth > max_depth:
                max_depth = depth
                deepest_dir = file_path.parent
    
    return deepest_dir

def get_package_from_directory_structure(existing_structure, main_source_dir, base_package):
    """Get the package name from directory structure"""
    if not existing_structure:
        return f"{base_package}.ui"
    
    try:
        # Get relative path from main source dir to existing structure
        relative_path = existing_structure.relative_to(main_source_dir)
        
        # Convert path to package notation
        if relative_path.parts:
            path_parts = list(relative_path.parts)
            base_parts = base_package.split('.')
            
            # If we have more path parts than base package parts,
            # the extra parts are subdirectories
            if len(path_parts) > len(base_parts):
                subdir_parts = path_parts[len(base_parts):]
                return f"{base_package}.{'.'.join(subdir_parts)}"
            else:
                # Use all path parts as subdirectories relative to base package
                return f"{base_package}.{'.'.join(path_parts)}"
    except ValueError:
        # Path is not relative to main_source_dir
        pass
    
    return f"{base_package}.ui"

def update_existing_compose_theme(theme_file, config):
    """Update existing Compose theme file"""
    # Check if this is a Color.kt file - if so, append new color variables
    if theme_file.name.lower() == 'color.kt':
        print(f"🔄 Appending new color variables to Color.kt: {theme_file}")
        
        # Read existing content
        with open(theme_file, 'r') as f:
            existing_content = f.read()
        
        # Generate new color variables for available MD3 colors
        branding = config["branding"]
        
        primary_color = hex_to_compose_color(
            branding.get("primary", "#6650a4")
        )
        secondary_color = hex_to_compose_color(
            branding.get("secondary", "#625b71")
        )
        background_color = hex_to_compose_color(
            branding.get("background", "#FFFBFE")
        )
        
        # Optional colors
        surface_color = hex_to_compose_color(
            branding.get("surface")
        ) if branding.get("surface") else None
        
        tertiary_color = hex_to_compose_color(
            branding.get("tertiary")
        ) if branding.get("tertiary") else None
        
        on_primary_color = hex_to_compose_color(
            branding.get("on_primary")
        ) if branding.get("on_primary") else None
        
        on_secondary_color = hex_to_compose_color(
            branding.get("on_secondary")
        ) if branding.get("on_secondary") else None
        
        on_tertiary_color = hex_to_compose_color(
            branding.get("on_tertiary")
        ) if branding.get("on_tertiary") else None
        
        on_background_color = hex_to_compose_color(
            branding.get("on_background")
        ) if branding.get("on_background") else None
        
        on_surface_color = hex_to_compose_color(
            branding.get("on_surface")
        ) if branding.get("on_surface") else None
        
        # Simple approach: Always add branded colors with "Brand" prefix
        # This ensures compatibility with any existing project structure
        has_brand_colors = '// FlavorFlow Branding Colors' in existing_content
        
        # Build new color variables to append
        new_variables = []
        
        if not has_brand_colors:
            new_variables.extend([
                '',
                '// FlavorFlow Branding Colors',
                '// Use these colors in your theme for consistent branding',
                '',
                f'val BrandPrimary = Color({primary_color})',
                f'val BrandSecondary = Color({secondary_color})',
                f'val BrandBackground = Color({background_color})',
                ''
            ])
            
            # Add optional colors if they exist in config
            if on_primary_color:
                new_variables.insert(-1, f'val BrandOnPrimary = Color({on_primary_color})')
            if on_secondary_color:
                new_variables.insert(-1, f'val BrandOnSecondary = Color({on_secondary_color})')
            if tertiary_color:
                new_variables.insert(-1, f'val BrandTertiary = Color({tertiary_color})')
            if on_tertiary_color:
                new_variables.insert(-1, f'val BrandOnTertiary = Color({on_tertiary_color})')
            if on_background_color:
                new_variables.insert(-1, f'val BrandOnBackground = Color({on_background_color})')
            if surface_color:
                new_variables.insert(-1, f'val BrandSurface = Color({surface_color})')
            if on_surface_color:
                new_variables.insert(-1, f'val BrandOnSurface = Color({on_surface_color})')
            
            # Add light and dark variants
            new_variables.extend([
                '// Light theme variants',
                f'val BrandLightPrimary = Color({primary_color})',
                f'val BrandLightSecondary = Color({secondary_color})',
                f'val BrandLightBackground = Color({background_color})',
                f'val BrandLightSurface = Color({surface_color or "0xFFFFFBFE"})',
                f'val BrandLightOnPrimary = Color({on_primary_color or "0xFFFFFFFF"})',
                f'val BrandLightOnSecondary = Color({on_secondary_color or "0xFFFFFFFF"})',
                f'val BrandLightOnBackground = Color({on_background_color or "0xFF1C1B1F"})',
                f'val BrandLightOnSurface = Color({on_surface_color or "0xFF1C1B1F"})',
                ''
            ])
            
            # Add tertiary colors if available
            if tertiary_color:
                new_variables.insert(-1, f'val BrandLightTertiary = Color({tertiary_color})')
                if on_tertiary_color:
                    new_variables.insert(-1, f'val BrandLightOnTertiary = Color({on_tertiary_color})')
                else:
                    new_variables.insert(-1, f'val BrandLightOnTertiary = Color(0xFFFFFFFF)')
            else:
                # Default tertiary colors for Material Design 3 compatibility
                new_variables.insert(-1, f'val BrandLightTertiary = Color(0xFF7D5260)')
                new_variables.insert(-1, f'val BrandLightOnTertiary = Color(0xFFFFFFFF)')
            
            # Dark theme variants with smart defaults
            new_variables.extend([
                '// Dark theme variants',
                f'val BrandDarkPrimary = Color({primary_color})',
                f'val BrandDarkSecondary = Color({secondary_color})',
                'val BrandDarkBackground = Color(0xFF121212)',
                'val BrandDarkSurface = Color(0xFF1C1B1F)',
                f'val BrandDarkOnPrimary = Color({on_primary_color or "0xFF000000"})',
                f'val BrandDarkOnSecondary = Color({on_secondary_color or "0xFF000000"})',
                'val BrandDarkOnBackground = Color(0xFFFFFFFF)',
                'val BrandDarkOnSurface = Color(0xFFE6E1E5)',
                ''
            ])
            
            # Add dark tertiary colors
            if tertiary_color:
                new_variables.insert(-1, f'val BrandDarkTertiary = Color({tertiary_color})')
                if on_tertiary_color:
                    new_variables.insert(-1, f'val BrandDarkOnTertiary = Color({on_tertiary_color})')
                else:
                    new_variables.insert(-1, f'val BrandDarkOnTertiary = Color(0xFF000000)')
            else:
                # Default dark tertiary colors
                new_variables.insert(-1, f'val BrandDarkTertiary = Color(0xFFEFB8C8)')
                new_variables.insert(-1, f'val BrandDarkOnTertiary = Color(0xFF000000)')
        
        
       
        
        if new_variables:
            # Append new variables to existing content
            updated_content = existing_content.rstrip() + '\n\n' + '\n'.join(new_variables) + '\n'
            
            # Write the updated content
            with open(theme_file, 'w') as f:
                f.write(updated_content)
                
            print(f"✓ Appended {len([v for v in new_variables if v.startswith('val')])} new color variables to Color.kt")
        else:
            print("✓ All required color variables already exist in Color.kt")
            
            # Even if variables exist, update their values with new branding colors
            with open(theme_file, 'r') as f:
                content = f.read()
            
            content = update_compose_colors(content, config)
            
            with open(theme_file, 'w') as f:
                f.write(content)
            
    else:
        # For other theme files, try to update using patterns
        with open(theme_file, 'r') as f:
            content = f.read()
        
        # Check if this is a Theme.kt file - handle it specially too
        if theme_file.name.lower() == 'theme.kt':
            print(f"🔄 Updating Theme.kt to use proper color variables: {theme_file}")
            
            # Use the robust update_compose_colors function for Theme.kt to handle corrupted syntax
            content = update_compose_colors(content, config)
        else:
            # Update color definitions based on common patterns
            content = update_compose_colors(content, config)
        
        with open(theme_file, 'w') as f:
            f.write(content)
        
        print(f"✓ Updated Compose theme file: {theme_file}")

def update_theme_kt_colors(content, config):
    """Update Theme.kt file to use Brand color variable references for complete Material Design 3 colors"""
    # Suppress unused parameter warning - config might be used in future enhancements
    _ = config
    
    # Replace lightColorScheme color assignments to use Brand variables
    light_color_mappings = [
        (r'(lightColorScheme\s*\([^)]*?)primary\s*=\s*[^,)]+', r'\1primary = BrandLightPrimary'),
        (r'(lightColorScheme\s*\([^)]*?)secondary\s*=\s*[^,)]+', r'\1secondary = BrandLightSecondary'),
        (r'(lightColorScheme\s*\([^)]*?)tertiary\s*=\s*[^,)]+', r'\1tertiary = BrandLightTertiary'),
        (r'(lightColorScheme\s*\([^)]*?)background\s*=\s*[^,)]+', r'\1background = BrandLightBackground'),
        (r'(lightColorScheme\s*\([^)]*?)surface\s*=\s*[^,)]+', r'\1surface = BrandLightSurface'),
        (r'(lightColorScheme\s*\([^)]*?)onPrimary\s*=\s*[^,)]+', r'\1onPrimary = BrandLightOnPrimary'),
        (r'(lightColorScheme\s*\([^)]*?)onSecondary\s*=\s*[^,)]+', r'\1onSecondary = BrandLightOnSecondary'),
        (r'(lightColorScheme\s*\([^)]*?)onTertiary\s*=\s*[^,)]+', r'\1onTertiary = BrandLightOnTertiary'),
        (r'(lightColorScheme\s*\([^)]*?)onBackground\s*=\s*[^,)]+', r'\1onBackground = BrandLightOnBackground'),
        (r'(lightColorScheme\s*\([^)]*?)onSurface\s*=\s*[^,)]+', r'\1onSurface = BrandLightOnSurface'),
    ]
    
    for pattern, replacement in light_color_mappings:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Replace darkColorScheme color assignments to use Brand variables
    dark_color_mappings = [
        (r'(darkColorScheme\s*\([^)]*?)primary\s*=\s*[^,)]+', r'\1primary = BrandDarkPrimary'),
        (r'(darkColorScheme\s*\([^)]*?)secondary\s*=\s*[^,)]+', r'\1secondary = BrandDarkSecondary'),
        (r'(darkColorScheme\s*\([^)]*?)tertiary\s*=\s*[^,)]+', r'\1tertiary = BrandDarkTertiary'),
        (r'(darkColorScheme\s*\([^)]*?)background\s*=\s*[^,)]+', r'\1background = BrandDarkBackground'),
        (r'(darkColorScheme\s*\([^)]*?)surface\s*=\s*[^,)]+', r'\1surface = BrandDarkSurface'),
        (r'(darkColorScheme\s*\([^)]*?)onPrimary\s*=\s*[^,)]+', r'\1onPrimary = BrandDarkOnPrimary'),
        (r'(darkColorScheme\s*\([^)]*?)onSecondary\s*=\s*[^,)]+', r'\1onSecondary = BrandDarkOnSecondary'),
        (r'(darkColorScheme\s*\([^)]*?)onTertiary\s*=\s*[^,)]+', r'\1onTertiary = BrandDarkOnTertiary'),
        (r'(darkColorScheme\s*\([^)]*?)onBackground\s*=\s*[^,)]+', r'\1onBackground = BrandDarkOnBackground'),
        (r'(darkColorScheme\s*\([^)]*?)onSurface\s*=\s*[^,)]+', r'\1onSurface = BrandDarkOnSurface'),
    ]
    
    for pattern, replacement in dark_color_mappings:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Add missing colors to lightColorScheme if they don't exist
    missing_light_colors = []
    if 'background = BrandLightBackground' not in content:
        missing_light_colors.append('background = BrandLightBackground')
    if 'surface = BrandLightSurface' not in content:
        missing_light_colors.append('surface = BrandLightSurface')
    if 'onPrimary = BrandLightOnPrimary' not in content:
        missing_light_colors.append('onPrimary = BrandLightOnPrimary')
    if 'onSecondary = BrandLightOnSecondary' not in content:
        missing_light_colors.append('onSecondary = BrandLightOnSecondary')
    if 'onTertiary = BrandLightOnTertiary' not in content:
        missing_light_colors.append('onTertiary = BrandLightOnTertiary')
    if 'onBackground = BrandLightOnBackground' not in content:
        missing_light_colors.append('onBackground = BrandLightOnBackground')
    if 'onSurface = BrandLightOnSurface' not in content:
        missing_light_colors.append('onSurface = BrandLightOnSurface')
    
    if missing_light_colors and 'lightColorScheme(' in content:
        # Find the last color assignment in lightColorScheme and add missing colors
        for color in missing_light_colors:
            content = re.sub(
                r'(lightColorScheme\s*\(\s*[^)]*?tertiary\s*=\s*[^,)]+)',
                rf'\1,\n    {color}',
                content,
                flags=re.DOTALL
            )
    
    # Add missing colors to darkColorScheme if they don't exist
    missing_dark_colors = []
    if 'background = BrandDarkBackground' not in content:
        missing_dark_colors.append('background = BrandDarkBackground')
    if 'surface = BrandDarkSurface' not in content:
        missing_dark_colors.append('surface = BrandDarkSurface')
    if 'onPrimary = BrandDarkOnPrimary' not in content:
        missing_dark_colors.append('onPrimary = BrandDarkOnPrimary')
    if 'onSecondary = BrandDarkOnSecondary' not in content:
        missing_dark_colors.append('onSecondary = BrandDarkOnSecondary')
    if 'onTertiary = BrandDarkOnTertiary' not in content:
        missing_dark_colors.append('onTertiary = BrandDarkOnTertiary')
    if 'onBackground = BrandDarkOnBackground' not in content:
        missing_dark_colors.append('onBackground = BrandDarkOnBackground')
    if 'onSurface = BrandDarkOnSurface' not in content:
        missing_dark_colors.append('onSurface = BrandDarkOnSurface')
    
    if missing_dark_colors and 'darkColorScheme(' in content:
        # Find the last color assignment in darkColorScheme and add missing colors
        for color in missing_dark_colors:
            content = re.sub(
                r'(darkColorScheme\s*\(\s*[^)]*?tertiary\s*=\s*[^,)]+)',
                rf'\1,\n    {color}',
                content,
                flags=re.DOTALL
            )
    
    # Set dynamicColor to false by default to use custom colors
    content = re.sub(
        r'dynamicColor:\s*Boolean\s*=\s*true',
        'dynamicColor: Boolean = false, // Set to false to use custom colors',
        content
    )
    
    return content

def update_compose_colors(content, config):
    """Update color definitions in Compose theme content - replaces entire color scheme blocks"""
    branding = config["branding"]
    
    # Helper function to get color with fallback to old field names
    def get_color(new_field, old_field):
        return branding.get(new_field) or branding.get(old_field)
    
    # Build complete light color scheme
    light_colors = []
    
    primary = get_color("primary", "primaryColor")
    if primary:
        light_colors.append(f'primary = Color({hex_to_compose_color(primary)})')
    
    on_primary = get_color("on_primary", "onPrimaryColor")
    if on_primary:
        light_colors.append(f'onPrimary = Color({hex_to_compose_color(on_primary)})')
    
    secondary = get_color("secondary", "secondaryColor")
    if secondary:
        light_colors.append(f'secondary = Color({hex_to_compose_color(secondary)})')
    
    on_secondary = get_color("on_secondary", "onSecondaryColor")
    if on_secondary:
        light_colors.append(f'onSecondary = Color({hex_to_compose_color(on_secondary)})')
    
    tertiary = get_color("tertiary", "tertiaryColor")
    if tertiary:
        light_colors.append(f'tertiary = Color({hex_to_compose_color(tertiary)})')
    
    on_tertiary = get_color("on_tertiary", "onTertiaryColor")
    if on_tertiary:
        light_colors.append(f'onTertiary = Color({hex_to_compose_color(on_tertiary)})')
    
    background = get_color("background", "backgroundColor")
    if background:
        light_colors.append(f'background = Color({hex_to_compose_color(background)})')
    
    on_background = get_color("on_background", "onBackgroundColor")
    if on_background:
        light_colors.append(f'onBackground = Color({hex_to_compose_color(on_background)})')
    
    surface = get_color("surface", "surfaceColor")
    if surface:
        light_colors.append(f'surface = Color({hex_to_compose_color(surface)})')
    
    on_surface = get_color("on_surface", "onSurfaceColor")
    if on_surface:
        light_colors.append(f'onSurface = Color({hex_to_compose_color(on_surface)})')
    
    # Build complete dark color scheme
    dark_colors = []
    
    if primary:
        dark_colors.append(f'primary = Color({hex_to_compose_color(primary)})')
    
    if on_primary:
        dark_colors.append(f'onPrimary = Color({hex_to_compose_color(on_primary)})')
    
    if secondary:
        dark_colors.append(f'secondary = Color({hex_to_compose_color(secondary)})')
    
    if on_secondary:
        dark_colors.append(f'onSecondary = Color({hex_to_compose_color(on_secondary)})')
    
    if tertiary:
        dark_colors.append(f'tertiary = Color({hex_to_compose_color(tertiary)})')
    
    if on_tertiary:
        dark_colors.append(f'onTertiary = Color({hex_to_compose_color(on_tertiary)})')
    
    # Use darker defaults for dark theme background
    dark_colors.append('background = Color(0xFF121212)')
    dark_colors.append('onBackground = Color(0xFFFFFFFF)')
    
    if surface:
        dark_colors.append('surface = Color(0xFF1C1B1F)')
    else:
        dark_colors.append('surface = Color(0xFF1C1B1F)')  # Default dark surface
    
    if on_surface:
        dark_colors.append('onSurface = Color(0xFFE6E1E5)')
    else:
        dark_colors.append('onSurface = Color(0xFFE6E1E5)')  # Default dark onSurface
    
    # Simple and robust replacement using multiline regex patterns
    if light_colors:
        light_scheme_content = ',\n    '.join(light_colors)
        new_light_scheme = f'private val LightColorScheme = lightColorScheme(\n    {light_scheme_content}\n)'
        
        # Replace everything from "private val LightColorScheme" to the next "private val" or "@Composable"
        light_pattern = r'private\s+val\s+LightColorScheme\s*=\s*lightColorScheme\s*\([^)]*(?:\([^)]*\)[^)]*)*(?:,\s*[^)]*)*\*?/?\s*\)\s*(?:,\s*[^)]*\*?/?\s*)*'
        
        # Try the multiline replacement
        new_content = re.sub(light_pattern, new_light_scheme, content, flags=re.DOTALL)
        
        # If the pattern didn't match (complex corruption), use a more aggressive approach
        if new_content == content and 'LightColorScheme' in content:
            # Find the start and manually find the end
            start_pattern = r'private\s+val\s+LightColorScheme'
            start_match = re.search(start_pattern, content)
            if start_match:
                start_idx = start_match.start()
                # Find the next major declaration
                remaining = content[start_idx:]
                end_pattern = r'\n\n\s*(?:private\s+val\s+\w+|@Composable|fun\s+\w+)'
                end_match = re.search(end_pattern, remaining)
                if end_match:
                    end_idx = start_idx + end_match.start()
                    content = content[:start_idx] + new_light_scheme + content[end_idx:]
                else:
                    # Last resort: replace a reasonable chunk
                    end_idx = start_idx + min(1000, len(remaining))
                    content = content[:start_idx] + new_light_scheme + '\n\n' + content[end_idx:].lstrip()
        else:
            content = new_content
    
    # Similar approach for dark color scheme
    if dark_colors:
        dark_scheme_content = ',\n    '.join(dark_colors)
        new_dark_scheme = f'private val DarkColorScheme = darkColorScheme(\n    {dark_scheme_content}\n)'
        
        # Replace everything from "private val DarkColorScheme" to the next "private val" or similar
        dark_pattern = r'private\s+val\s+DarkColorScheme\s*=\s*darkColorScheme\s*\([^)]*(?:\([^)]*\)[^)]*)*(?:,\s*[^)]*)*\*?/?\s*\)\s*'
        
        # Try the multiline replacement
        new_content = re.sub(dark_pattern, new_dark_scheme, content, flags=re.DOTALL)
        
        # If the pattern didn't match, use the aggressive approach
        if new_content == content and 'DarkColorScheme' in content:
            start_pattern = r'private\s+val\s+DarkColorScheme'
            start_match = re.search(start_pattern, content)
            if start_match:
                start_idx = start_match.start()
                remaining = content[start_idx:]
                end_pattern = r'\n\n\s*(?:private\s+val\s+\w+|@Composable|fun\s+\w+)'
                end_match = re.search(end_pattern, remaining)
                if end_match:
                    end_idx = start_idx + end_match.start()
                    content = content[:start_idx] + new_dark_scheme + content[end_idx:]
                else:
                    end_idx = start_idx + min(1000, len(remaining))
                    content = content[:start_idx] + new_dark_scheme + '\n\n' + content[end_idx:].lstrip()
        else:
            content = new_content
    
    # Update individual color definitions
    patterns = [
        (r'^val\s+BrandPrimary\s*=\s*Color\([^)]+\)', f'val BrandPrimary = Color({hex_to_compose_color(branding.get("primary", "#6650a4"))})'),
        (r'^val\s+BrandSecondary\s*=\s*Color\([^)]+\)', f'val BrandSecondary = Color({hex_to_compose_color(branding.get("secondary", "#625b71"))})'),
        (r'^val\s+BrandBackground\s*=\s*Color\([^)]+\)', f'val BrandBackground = Color({hex_to_compose_color(branding.get("background", "#FFFBFE"))})'),
    ]
    
    # Apply patterns for individual color definitions
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

def hex_to_compose_color(hex_color):
    """Convert hex color to Compose Color format"""
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Add alpha channel if not present (ARGB format)
    if len(hex_color) == 6:
        hex_color = 'FF' + hex_color
    
    return f'0x{hex_color}'

def create_compose_theme_files(config):
    """Create new Compose theme files if none exist"""
    app_module = find_android_app_module()  # This will use cached result
    
    # Find the main source directory
    source_dirs = [JAVA_SOURCE_DIR, KOTLIN_SOURCE_DIR]
    main_source_dir = None
    
    for source_dir in source_dirs:
        source_path = app_module / source_dir
        if source_path.exists():
            main_source_dir = source_path
            break
    
    if not main_source_dir:
        print(f"⚠ No source directory found, creating in {app_module}/{JAVA_SOURCE_DIR}")
        main_source_dir = app_module / JAVA_SOURCE_DIR
    
    # Always create theme files in ui.theme subdirectory structure
    # First check if there's already a ui.theme structure we should preserve
    package_path = config["packageName"].replace('.', '/')
    
    # Look for existing ui/theme structure
    existing_ui_theme_dir = main_source_dir / package_path / 'ui' / 'theme'
    if existing_ui_theme_dir.exists():
        print(f"📱 Found existing ui/theme structure at: {existing_ui_theme_dir}")
        theme_dir = existing_ui_theme_dir
        package_with_subdir = f'{config["packageName"]}.ui'
    else:
        # Check if there's any existing theme structure with different subdirectories
        existing_structure = detect_existing_theme_structure(main_source_dir, package_path)
        if existing_structure:
            print(f"📱 Found existing theme structure at: {existing_structure}")
            theme_dir = existing_structure / 'theme'
            package_with_subdir = get_package_from_theme_structure(existing_structure, main_source_dir, config["packageName"])
        else:
            # Default to ui.theme structure
            print("📱 Creating new ui/theme structure")
            theme_dir = main_source_dir / package_path / 'ui' / 'theme'
            package_with_subdir = f'{config["packageName"]}.ui'
    
    print(f"📁 Using theme directory: {theme_dir}")
    os.makedirs(theme_dir, exist_ok=True)
    
    # Create Color.kt file
    create_compose_color_file(theme_dir, config, package_with_subdir)
    
    # Only create Theme.kt file if it doesn't already exist
    # Existing Theme.kt files are preserved with their original function names
    # and only their color schemes are updated via update_existing_compose_theme()
    theme_kt_file = theme_dir / 'Theme.kt'
    if not theme_kt_file.exists():
        create_compose_theme_file(theme_dir, config, package_with_subdir)
        print(f"✓ Created new Theme.kt file with {config['appName'].replace(' ', '')}Theme function")
    else:
        print(f"✓ Preserved existing Theme.kt file (function name and structure maintained)")
    
    # Create Type.kt file (Typography)
    create_compose_typography_file(theme_dir, config, package_with_subdir)
    
    print(f"✓ Created Compose theme files in: {theme_dir}")

def detect_existing_theme_structure(main_source_dir, package_path):
    """Detect existing theme-related file structure specifically"""
    base_package_dir = main_source_dir / package_path
    
    if not base_package_dir.exists():
        return None
    
    # Look for theme-related files in subdirectories
    for subdir in base_package_dir.rglob('*'):
        if subdir.is_dir():
            # Check if this directory contains theme files
            theme_files = list(subdir.glob('*Theme*.kt')) + list(subdir.glob('*Color*.kt')) + list(subdir.glob('*Type*.kt'))
            if theme_files and 'theme' in subdir.name.lower():
                # Found theme files in a theme directory
                return subdir.parent
    
    return None

def get_package_from_theme_structure(theme_structure, main_source_dir, base_package):
    """Get package name from theme directory structure"""
    try:
        relative_path = theme_structure.relative_to(main_source_dir)
        package_parts = base_package.split('.')
        
        # Remove base package parts from path
        path_parts = list(relative_path.parts)
        if len(path_parts) > len(package_parts):
            subdir_parts = path_parts[len(package_parts):]
            return f"{base_package}.{'.'.join(subdir_parts)}"
    except ValueError:
        pass
    
    return f"{base_package}.ui"

def create_compose_color_file(theme_dir, config, package_name=None):
    """Create Color.kt file for Compose"""
    if package_name is None:
        package_name = f'{config["packageName"]}.ui.theme'
    else:
        package_name = f'{package_name}.theme'
    
    # Extract required color values from config
    branding = config["branding"]
    primary_color = hex_to_compose_color(
        branding.get("primary", "#6650a4")
    )
    secondary_color = hex_to_compose_color(
        branding.get("secondary", "#625b71")
    )
    background_color = hex_to_compose_color(
        branding.get("background", "#FFFBFE")
    )
    
    # Extract optional color values
    on_primary_color = hex_to_compose_color(
        branding.get("on_primary")
    ) if branding.get("on_primary") else None
    
    on_secondary_color = hex_to_compose_color(
        branding.get("on_secondary")
    ) if branding.get("on_secondary") else None
    
    tertiary_color = hex_to_compose_color(
        branding.get("tertiary")
    ) if branding.get("tertiary") else None
    
    on_tertiary_color = hex_to_compose_color(
        branding.get("on_tertiary")
    ) if branding.get("on_tertiary") else None
    
    on_background_color = hex_to_compose_color(
        branding.get("on_background")
    ) if branding.get("on_background") else None
    surface_color = hex_to_compose_color(branding.get("surface")) if branding.get("surface") else None
    on_surface_color = hex_to_compose_color(branding.get("on_surface")) if branding.get("on_surface") else None
    
    # Build color content dynamically based on available colors
    color_lines = [
        f'package {package_name}',
        '',
        'import androidx.compose.ui.graphics.Color',
        '',
        '// Primary colors',
        f'val Primary = Color({primary_color})'
    ]
    
    if on_primary_color:
        color_lines.append(f'val OnPrimary = Color({on_primary_color})')
    
    color_lines.extend([
        '',
        '// Secondary colors',
        f'val Secondary = Color({secondary_color})'
    ])
    
    if on_secondary_color:
        color_lines.append(f'val OnSecondary = Color({on_secondary_color})')
    
    if tertiary_color:
        color_lines.extend([
            '',
            '// Tertiary colors',
            f'val Tertiary = Color({tertiary_color})'
        ])
        if on_tertiary_color:
            color_lines.append(f'val OnTertiary = Color({on_tertiary_color})')
    
    color_lines.extend([
        '',
        '// Background colors',
        f'val Background = Color({background_color})'
    ])
    
    if on_background_color:
        color_lines.append(f'val OnBackground = Color({on_background_color})')
    
    if surface_color:
        color_lines.extend([
            '',
            '// Surface colors',
            f'val Surface = Color({surface_color})'
        ])
        if on_surface_color:
            color_lines.append(f'val OnSurface = Color({on_surface_color})')
    
    # Light theme colors
    color_lines.extend([
        '',
        '// Light theme colors',
        f'val LightPrimary = Color({primary_color})',
        f'val LightSecondary = Color({secondary_color})',
        f'val LightBackground = Color({background_color})'
    ])
    
    if on_primary_color:
        color_lines.insert(-2, f'val LightOnPrimary = Color({on_primary_color})')
    if on_secondary_color:
        color_lines.insert(-1, f'val LightOnSecondary = Color({on_secondary_color})')
    if tertiary_color:
        color_lines.append(f'val LightTertiary = Color({tertiary_color})')
    if on_tertiary_color:
        color_lines.append(f'val LightOnTertiary = Color({on_tertiary_color})')
    if on_background_color:
        color_lines.append(f'val LightOnBackground = Color({on_background_color})')
    if surface_color:
        color_lines.append(f'val LightSurface = Color({surface_color})')
    if on_surface_color:
        color_lines.append(f'val LightOnSurface = Color({on_surface_color})')
    
    # Dark theme colors
    color_lines.extend([
        '',
        '// Dark theme colors (you can customize these)',
        f'val DarkPrimary = Color({primary_color})',
        f'val DarkSecondary = Color({secondary_color})',
        'val DarkBackground = Color(0xFF121212)',
        'val DarkOnBackground = Color(0xFFFFFFFF)'
    ])
    
    if on_primary_color:
        color_lines.insert(-3, f'val DarkOnPrimary = Color({on_primary_color})')
    if on_secondary_color:
        color_lines.insert(-3, f'val DarkOnSecondary = Color({on_secondary_color})')
    if tertiary_color:
        color_lines.insert(-2, f'val DarkTertiary = Color({tertiary_color})')
    if on_tertiary_color:
        color_lines.insert(-2, f'val DarkOnTertiary = Color({on_tertiary_color})')
    if surface_color:
        color_lines.extend([
            'val DarkSurface = Color(0xFF1C1B1F)',
            'val DarkOnSurface = Color(0xFFE6E1E5)'
        ])
    
    # Brand colors
    color_lines.extend([
        '',
        '// Additional brand colors',
        f'val BrandPrimary = Color({primary_color})',
        f'val BrandSecondary = Color({secondary_color})',
        f'val BrandBackground = Color({background_color})'
    ])
    
    if on_primary_color:
        color_lines.insert(-2, f'val BrandOnPrimary = Color({on_primary_color})')
    if on_secondary_color:
        color_lines.insert(-1, f'val BrandOnSecondary = Color({on_secondary_color})')
    if tertiary_color:
        color_lines.append(f'val BrandTertiary = Color({tertiary_color})')
    if on_tertiary_color:
        color_lines.append(f'val BrandOnTertiary = Color({on_tertiary_color})')
    if on_background_color:
        color_lines.append(f'val BrandOnBackground = Color({on_background_color})')
    if surface_color:
        color_lines.append(f'val BrandSurface = Color({surface_color})')
    if on_surface_color:
        color_lines.append(f'val BrandOnSurface = Color({on_surface_color})')
    
    color_content = '\n'.join(color_lines) + '\n'
    
    color_file = theme_dir / 'Color.kt'
    with open(color_file, 'w') as f:
        f.write(color_content)

def create_compose_theme_file(theme_dir, config, package_name=None):
    """Create Theme.kt file for Compose"""
    if package_name is None:
        package_name = f'{config["packageName"]}.ui.theme'
    else:
        package_name = f'{package_name}.theme'
    
    app_name = config["appName"].replace(' ', '')
    branding = config["branding"]
    
    # Build light color scheme using Brand variable names
    light_colors = [
        'primary = BrandLightPrimary',
        'secondary = BrandLightSecondary',
        'background = BrandLightBackground'
    ]
    
    if branding.get("on_primary") or branding.get("onPrimaryColor"):
        light_colors.insert(1, 'onPrimary = BrandLightOnPrimary')
    if branding.get("on_secondary") or branding.get("onSecondaryColor"):
        light_colors.insert(-1, 'onSecondary = BrandLightOnSecondary')
    if branding.get("tertiary") or branding.get("tertiaryColor"):
        light_colors.append('tertiary = BrandLightTertiary')
    if branding.get("on_tertiary") or branding.get("onTertiaryColor"):
        light_colors.append('onTertiary = BrandLightOnTertiary')
    if branding.get("on_background") or branding.get("onBackgroundColor"):
        light_colors.append('onBackground = BrandLightOnBackground')
    if branding.get("surface") or branding.get("surfaceColor"):
        light_colors.append('surface = BrandLightSurface')
    if branding.get("on_surface") or branding.get("onSurfaceColor"):
        light_colors.append('onSurface = BrandLightOnSurface')
    
    # Build dark color scheme using Brand variable names
    dark_colors = [
        'primary = BrandDarkPrimary',
        'secondary = BrandDarkSecondary',
        'background = BrandDarkBackground',
        'onBackground = BrandDarkOnBackground'
    ]
    
    if branding.get("on_primary") or branding.get("onPrimaryColor"):
        dark_colors.insert(1, 'onPrimary = BrandDarkOnPrimary')
    if branding.get("on_secondary") or branding.get("onSecondaryColor"):
        dark_colors.insert(-2, 'onSecondary = BrandDarkOnSecondary')
    if branding.get("tertiary") or branding.get("tertiaryColor"):
        dark_colors.insert(-2, 'tertiary = BrandDarkTertiary')
    if branding.get("on_tertiary") or branding.get("onTertiaryColor"):
        dark_colors.insert(-2, 'onTertiary = BrandDarkOnTertiary')
    if branding.get("surface") or branding.get("surfaceColor"):
        dark_colors.extend(['surface = BrandDarkSurface', 'onSurface = BrandDarkOnSurface'])
    
    light_scheme = ',\n    '.join(light_colors)
    dark_scheme = ',\n    '.join(dark_colors)
    
    theme_content = f'''package {package_name}

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColorScheme = lightColorScheme(
    {light_scheme}
)

private val DarkColorScheme = darkColorScheme(
    {dark_scheme}
)

@Composable
fun {app_name}Theme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = false, // Disabled to use custom branding colors
    content: @Composable () -> Unit
) {{
    val colorScheme = when {{
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {{
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }}
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }}
    
    val view = LocalView.current
    if (!view.isInEditMode) {{
        SideEffect {{
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = darkTheme
        }}
    }}

    MaterialTheme(
        colorScheme = colorScheme,
        content = content
    )
}}
'''
    
    theme_file = theme_dir / 'Theme.kt'
    with open(theme_file, 'w') as f:
        f.write(theme_content)

def create_compose_typography_file(theme_dir, config, package_name=None):
    """Create Type.kt file for Compose Typography"""
    if package_name is None:
        package_name = f'{config["packageName"]}.ui.theme'
    else:
        package_name = f'{package_name}.theme'
    
    typography_content = f'''package {package_name}

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// Set of Material typography styles to start with
val Typography = Typography(
    bodyLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.5.sp
    ),
    titleLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Normal,
        fontSize = 22.sp,
        lineHeight = 28.sp,
        letterSpacing = 0.sp
    ),
    labelSmall = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.Medium,
        fontSize = 11.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.5.sp
    )
)
'''
    
    typography_file = theme_dir / 'Type.kt'
    with open(typography_file, 'w') as f:
        f.write(typography_content)

def update_package_name(config):
    """Update package name in build.gradle and AndroidManifest.xml"""
    app_module = find_android_app_module()  # This will use cached result
    
    # Update build.gradle
    build_gradle_path = app_module / 'build.gradle.kts'
    if not build_gradle_path.exists():
        build_gradle_path = app_module / 'build.gradle'
    
    if build_gradle_path.exists():
        with open(build_gradle_path, 'r') as f:
            content = f.read()
        
        # Replace applicationId
        pattern = r'applicationId\s*[=:]\s*["\'][^"\']*["\']'
        replacement = f'applicationId = "{config["packageName"]}"'
        content = re.sub(pattern, replacement, content)
        
        # Replace namespace (for newer Gradle versions)
        namespace_pattern = r'namespace\s*[=:]\s*["\'][^"\']*["\']'
        namespace_replacement = f'namespace = "{config["packageName"]}"'
        content = re.sub(namespace_pattern, namespace_replacement, content)
        
        with open(build_gradle_path, 'w') as f:
            f.write(content)
        print(f"✓ Updated package name and namespace in build.gradle to: {config['packageName']}")
    
    # Update AndroidManifest.xml
    manifest_path = get_app_source_path('src/main/AndroidManifest.xml')
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            content = f.read()
        
        # Replace package attribute
        pattern = r'package\s*=\s*["\'][^"\']*["\']'
        replacement = f'package="{config["packageName"]}"'
        content = re.sub(pattern, replacement, content)
        
        with open(manifest_path, 'w') as f:
            f.write(content)
        print(f"✓ Updated package name in AndroidManifest.xml to: {config['packageName']}")

def restructure_source_directories(config):
    """Restructure source directories to match the new package name"""
    app_module = find_android_app_module()  # This will use cached result
    
    # Define source directories to process
    source_dirs = [
        JAVA_SOURCE_DIR,
        KOTLIN_SOURCE_DIR,
        TEST_JAVA_SOURCE_DIR,
        TEST_KOTLIN_SOURCE_DIR,
        ANDROID_TEST_JAVA_SOURCE_DIR,
        ANDROID_TEST_KOTLIN_SOURCE_DIR
    ]
    
    new_package = config["packageName"]
    new_package_path = new_package.replace('.', '/')
    
    # First, get the old package name by examining existing files
    old_package = detect_old_package_name(app_module, source_dirs)
    
    if old_package and old_package != new_package:
        print(f"🔄 Detected old package: {old_package}")
        print(f"🔄 Updating to new package: {new_package}")
        
        # Update all files with package references throughout the entire project
        update_all_package_references(app_module, old_package, new_package)
    
    # Then handle the directory restructuring
    for source_dir in source_dirs:
        source_path = app_module / source_dir
        if not source_path.exists():
            continue
            
        print(f"🔄 Processing {source_path}...")
        
        # Find the old package root directory
        old_package_root = find_old_package_root_in_source(source_path, old_package)
        
        if old_package_root and old_package_root.exists():
            # Calculate new package root
            new_package_root = source_path / new_package_path
            
            # Move the entire package structure preserving subdirectories
            move_package_structure(old_package_root, new_package_root, new_package)
        else:
            # No existing packages found, create the new structure
            new_package_dir = source_path / new_package_path
            os.makedirs(new_package_dir, exist_ok=True)
            print(f"✓ Created new package directory: {new_package_dir}")

def find_old_package_root_in_source(source_path, old_package):
    """Find the root directory of the old package in a source directory"""
    if not old_package:
        return None
    
    # Try direct path first
    old_package_path = old_package.replace('.', '/')
    old_package_root = source_path / old_package_path
    
    if old_package_root.exists():
        return old_package_root
    
    # If direct path doesn't exist, search for files with the old package
    return find_package_root_from_files(source_path, old_package)

def find_package_root_from_files(source_path, old_package):
    """Find package root by examining source files"""
    for file_path in source_path.rglob('*.kt'):
        if file_path.is_file():
            package_root = extract_package_root_from_file(file_path, old_package)
            if package_root:
                return package_root
    return None

def extract_package_root_from_file(file_path, old_package):
    """Extract package root directory from a single file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        package_match = re.search(PACKAGE_PATTERN, content, re.MULTILINE)
        if package_match and package_match.group(1).startswith(old_package):
            package_name = package_match.group(1)
            relative_package = package_name[len(old_package):].lstrip('.')
            
            if relative_package:
                # File is in a subdirectory, walk up to find package root
                return walk_up_to_package_root(file_path, relative_package)
            else:
                # File is in the root package
                return file_path.parent
                
    except Exception as e:
        print(f"⚠ Error reading {file_path}: {e}")
    
    return None

def walk_up_to_package_root(file_path, relative_package):
    """Walk up directory tree to find package root"""
    current_dir = file_path.parent
    levels = len(relative_package.split('.'))
    
    for _ in range(levels):
        if current_dir.parent != current_dir:
            current_dir = current_dir.parent
        else:
            break
    
    return current_dir

def move_package_structure(old_package_root, new_package_root, new_package):
    """Move entire package structure while preserving subdirectories"""
    if not old_package_root.exists():
        return
    
    print(f"  🔄 Moving package structure from {old_package_root} to {new_package_root}")
    
    # Create new package root
    os.makedirs(new_package_root, exist_ok=True)
    
    # Move all contents recursively
    moved_items = 0
    
    for item in old_package_root.rglob('*'):
        if item.is_file():
            # Calculate relative path from old package root
            relative_path = item.relative_to(old_package_root)
            new_item_path = new_package_root / relative_path
            
            # Create directory structure if needed
            os.makedirs(new_item_path.parent, exist_ok=True)
            
            if item.suffix in SOURCE_EXTENSIONS:
                # Update source files
                with open(item, 'r') as f:
                    content = f.read()
                
                # Update package declaration preserving subdirectory
                content = update_package_declaration_with_subdir(content, new_package, relative_path.parent)
                
                # Write to new location
                with open(new_item_path, 'w') as f:
                    f.write(content)
                
                print(f"    ✓ Moved {relative_path} with updated package")
            else:
                # Copy non-source files as-is
                import shutil
                shutil.copy2(item, new_item_path)
                print(f"    ✓ Copied {relative_path}")
            
            moved_items += 1
            # Remove old file
            item.unlink()
    
    if moved_items > 0:
        # Clean up old empty directories
        cleanup_old_package_structure(old_package_root)
        print(f"  ✅ Moved {moved_items} items preserving directory structure")

def detect_old_package_name(app_module, source_dirs):
    """Detect the current package name from existing source files"""
    for source_dir in source_dirs:
        package_name = find_package_in_directory(app_module / source_dir)
        if package_name:
            return package_name
    return None

def find_package_in_directory(source_path):
    """Find package name in a specific directory"""
    if not source_path.exists():
        return None
        
    # Look for any source file to extract package name
    for file_path in source_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in SOURCE_EXTENSIONS:
            package_name = extract_package_from_file(file_path)
            if package_name:
                return package_name
    return None

def extract_package_from_file(file_path):
    """Extract package name from a single source file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract package declaration
        package_match = re.search(PACKAGE_PATTERN, content, re.MULTILINE)
        return package_match.group(1) if package_match else None
        
    except Exception as e:
        print(f"⚠ Error reading {file_path}: {e}")
        return None

def update_all_package_references(app_module, old_package, new_package):
    """Update package references in all files throughout the entire project"""
    print(f"🔄 Updating package references from {old_package} to {new_package} in all project files...")
    
    # Start from the project root directory (parent of app module)
    project_root = app_module.parent if app_module.name != '.' else Path('.')
    
    files_updated = 0
    
    # Process all text files in the entire project
    for file_path in project_root.rglob('*'):
        if file_path.is_file() and is_text_file(file_path):
            if update_package_references_in_any_file(file_path, old_package, new_package):
                files_updated += 1
                print(f"    ✓ Updated references in {file_path.relative_to(project_root)}")
    
    print(f"✓ Updated package references in {files_updated} files across the entire project")

def is_text_file(file_path):
    """Check if a file is a text file that might contain package references"""
    # Skip binary files and certain directories
    skip_patterns = [
        '.git', '.gradle', 'build', 'bin', 'obj', 'target', 'out',
        'node_modules', '.idea', '.vscode', '__pycache__', 'dist'
    ]
    
    # Check if file is in a directory we should skip
    for part in file_path.parts:
        if part in skip_patterns:
            return False
    
    # Check file extensions that typically contain text
    text_extensions = {
        '.kt', '.java', '.xml', '.json', '.gradle', '.kts', '.properties',
        '.md', '.txt', '.yml', '.yaml', '.toml', '.pro', '.cfg', '.conf',
        '.sh', '.bat', '.py', '.js', '.ts', '.html', '.css', '.scss'
    }
    
    # Check if file has a text extension
    if file_path.suffix.lower() in text_extensions:
        return True
    
    # Check if file has no extension but might be text (like gradlew)
    if not file_path.suffix and file_path.name in ['gradlew', 'Dockerfile', 'Makefile']:
        return True
    
    return False

def update_package_references_in_any_file(file_path, old_package, new_package):
    """Update package references in any file (simplified global replace)"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()
        
        # Simple string replacement of old package with new package
        updated_content = original_content.replace(old_package, new_package)
        
        # Only write if content changed
        if updated_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True
            
    except Exception as e:
        print(f"    ⚠ Error updating {file_path}: {e}")
    
    return False

def update_references_in_directory(source_path, old_package, new_package):
    """Update package references in all files within a directory"""
    if not source_path.exists():
        return 0
        
    files_updated = 0
    
    # Process all source files in this directory
    for file_path in source_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in SOURCE_EXTENSIONS:
            if update_references_in_file(file_path, old_package, new_package):
                files_updated += 1
                print(f"    ✓ Updated references in {file_path.name}")
    
    return files_updated

def update_references_in_file(file_path, old_package, new_package):
    """Update package references in a single file"""
    try:
        with open(file_path, 'r') as f:
            original_content = f.read()
        
        # Update package references
        updated_content = update_package_references_in_content(original_content, old_package, new_package)
        
        # Only write if content changed
        if updated_content != original_content:
            with open(file_path, 'w') as f:
                f.write(updated_content)
            return True
            
    except Exception as e:
        print(f"    ⚠ Error updating {file_path}: {e}")
    
    return False

def update_package_references_in_content(content, old_package, new_package):
    """Update package references in file content without changing package declaration"""
    # Update import statements
    content = update_import_statements(content, old_package, new_package)
    
    # Update inline class references
    content = update_inline_class_references(content, old_package, new_package)
    
    # Update string literals
    content = update_string_literals(content, old_package, new_package)
    
    return content

def find_existing_packages(source_path):
    """Find existing package directories that contain source files"""
    existing_packages = []
    
    if not source_path.exists():
        return existing_packages
    
    # Look for directories that contain .kt or .java files
    for item in source_path.rglob('*'):
        if item.is_file() and item.suffix in SOURCE_EXTENSIONS:
            # Get the package directory (parent of the file)
            package_dir = item.parent
            if package_dir not in existing_packages and package_dir != source_path:
                existing_packages.append(package_dir)
    
    return existing_packages

def move_source_files(old_package_dir, new_package_dir, new_package):
    """Move source files and update package declarations while preserving subdirectory structure"""
    if not old_package_dir.exists():
        return
    
    print(f"  🔄 Moving files from {old_package_dir} to {new_package_dir}")
    
    # Create new package directory
    os.makedirs(new_package_dir, exist_ok=True)
    
    # Move all files and subdirectories recursively
    moved_files = []
    
    for item in old_package_dir.rglob('*'):
        if item.is_file():
            # Calculate relative path from old package dir
            relative_path = item.relative_to(old_package_dir)
            new_file_path = new_package_dir / relative_path
            
            # Create directory structure if needed
            os.makedirs(new_file_path.parent, exist_ok=True)
            
            if item.suffix in SOURCE_EXTENSIONS:
                # Read and update source files
                with open(item, 'r') as f:
                    content = f.read()
                
                # Update package declaration to preserve subdirectory structure
                content = update_package_declaration_with_subdir(content, new_package, relative_path.parent)
                
                # Write to new location
                with open(new_file_path, 'w') as f:
                    f.write(content)
                
                print(f"    ✓ Moved {relative_path} with updated package")
                moved_files.append(str(relative_path))
            else:
                # Copy non-source files as-is
                import shutil
                shutil.copy2(item, new_file_path)
                print(f"    ✓ Copied {relative_path}")
                moved_files.append(str(relative_path))
            
            # Remove old file
            item.unlink()
    
    if moved_files:
        # Get the root of the old package structure to clean up
        old_package_root = get_old_package_root(old_package_dir)
        
        # Remove old empty directories starting from the deepest level
        cleanup_old_package_structure(old_package_root)
        
        print(f"  🗑️ Cleaned up old package structure starting from {old_package_root}")
        print(f"  ✅ Moved {len(moved_files)} files preserving subdirectory structure")

def update_package_declaration_with_subdir(content, new_base_package, subdir_path):
    """Update package declaration while preserving subdirectory structure"""
    # Build the full package name including subdirectories
    if subdir_path and subdir_path.parts:
        # Convert subdirectory path to package notation
        subdir_package = '.'.join(subdir_path.parts)
        full_package = f"{new_base_package}.{subdir_package}"
    else:
        full_package = new_base_package
    
    # First, extract the old package name from the current content
    old_package_match = re.search(PACKAGE_PATTERN, content, re.MULTILINE)
    old_package = old_package_match.group(1) if old_package_match else None
    
    if old_package and old_package != full_package:
        print(f"      🔄 Updating package from {old_package} to {full_package}")
        
        # Update package declaration
        content = re.sub(
            PACKAGE_PATTERN,
            f'package {full_package}',
            content,
            flags=re.MULTILINE
        )
        
        # Update import statements that reference the old package
        content = update_import_statements(content, old_package, full_package)
        
        # Update inline class references 
        content = update_inline_class_references(content, old_package, full_package)
        
        # Update string literals
        content = update_string_literals(content, old_package, full_package)
    
    return content

def update_package_declaration(content, new_package):
    """Update package declaration and all references to old package in source files"""
    # First, extract the old package name from the current content
    old_package_match = re.search(PACKAGE_PATTERN, content, re.MULTILINE)
    old_package = old_package_match.group(1) if old_package_match else None
    
    if old_package and old_package != new_package:
        print(f"    🔄 Updating package references from {old_package} to {new_package}")
        
        # Update package declaration
        content = re.sub(
            r'^package\s+[a-zA-Z][a-zA-Z0-9_.]*',
            f'package {new_package}',
            content,
            flags=re.MULTILINE
        )
        
        # Update import statements
        content = update_import_statements(content, old_package, new_package)
        
        # Update inline class references (e.g., R.string.app_name -> new.package.R.string.app_name)
        content = update_inline_class_references(content, old_package, new_package)
        
        # Update any string literals that contain the old package (e.g., in manifests or configurations)
        content = update_string_literals(content, old_package, new_package)
    
    return content

def update_import_statements(content, old_package, new_package):
    """Update import statements that reference the old package"""
    # Update direct imports of the old package
    pattern = r'^import\s+' + re.escape(old_package) + r'(\.[\w.]*)?'
    replacement = f'import {new_package}\\1'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Update static imports
    pattern = r'^import\s+static\s+' + re.escape(old_package) + r'(\.[\w.]*)?'
    replacement = f'import static {new_package}\\1'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

def update_inline_class_references(content, old_package, new_package):
    """Update inline references to classes from the old package"""
    # Simply replace any occurrence of the old package with the new package
    content = content.replace(old_package, new_package)
    
    return content

def update_string_literals(content, old_package, new_package):
    """Update string literals that contain the old package name"""
    # Update package name in string literals (common in manifest files, configurations, etc.)
    # Be careful to only replace when it's clearly a package reference
    patterns = [
        # Quoted package names
        (f'"{re.escape(old_package)}"', f'"{new_package}"'),
        (f"'{re.escape(old_package)}'", f"'{new_package}'"),
        
        # Package names in XML attributes (for AndroidManifest.xml, etc.)
        (f'package="{re.escape(old_package)}"', f'package="{new_package}"'),
        (f"package='{re.escape(old_package)}'", f"package='{new_package}'"),
        
        # Application ID references
        (f'applicationId\\s*=\\s*"{re.escape(old_package)}"', f'applicationId = "{new_package}"'),
        (f"applicationId\\s*=\\s*'{re.escape(old_package)}'", f"applicationId = '{new_package}'"),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def get_old_package_root(package_dir):
    """Get the root directory of the old package structure to clean up"""
    # Walk up the directory tree to find the first directory that contains source files
    # or is at the source root level (src/main/java, src/main/kotlin, etc.)
    current_dir = package_dir
    
    while current_dir.parent != current_dir:  # Not at filesystem root
        parent = current_dir.parent
        
        # Check if we're at a source root directory
        if parent.name in ['java', 'kotlin'] and parent.parent.name == 'main':
            break
            
        # Check if parent has other source files (indicating it's shared)
        has_other_files = any(
            f.suffix in SOURCE_EXTENSIONS 
            for f in parent.rglob('*') 
            if f.is_file() and f != current_dir
        )
        
        if has_other_files:
            break
            
        current_dir = parent
    
    return current_dir

def cleanup_old_package_structure(start_dir):
    """Remove old package directories recursively, starting from the deepest level"""
    if not start_dir.exists() or not start_dir.is_dir():
        return
    
    # First, recursively clean up subdirectories
    for subdir in start_dir.iterdir():
        if subdir.is_dir():
            cleanup_old_package_structure(subdir)
    
    # Then check if this directory is now empty and can be removed
    try:
        if start_dir.exists() and start_dir.is_dir():
            # Check if directory is empty
            contents = list(start_dir.iterdir())
            if not contents:
                # Don't remove source root directories
                if start_dir.name not in ['java', 'kotlin', 'main', 'src', 'test', 'androidTest']:
                    start_dir.rmdir()
                    print(f"    🗑️ Removed empty directory: {start_dir}")
    except OSError as e:
        # Directory not empty or permission error
        print(f"    ⚠ Could not remove directory {start_dir}: {e}")

def cleanup_empty_directories(directory):
    """Remove empty directories recursively"""
    try:
        if directory.exists() and directory.is_dir():
            # Remove empty subdirectories first
            for subdir in directory.iterdir():
                if subdir.is_dir():
                    cleanup_empty_directories(subdir)
            
            # Remove this directory if it's empty
            if not any(directory.iterdir()):
                directory.rmdir()
                print(f"  🗑️ Removed empty directory: {directory}")
    except OSError:
        # Directory not empty or other error
        pass

def generate_app_icons(config):
    """Generate launcher icons from logo and update AndroidManifest"""
    # Check if logo path is provided and not empty
    logo_path_str = config["branding"].get("logoPath", "").strip()
    if not logo_path_str:
        print("⚠ No logo provided, skipping launcher icon generation")
        return
    
    logo_path = Path(logo_path_str)
    if not logo_path.exists():
        print(f"⚠ Logo file not found: {logo_path}, skipping launcher icon generation")
        return
    
    # Generate launcher icons
    generate_launcher_icons(logo_path, config)
    
    # Update AndroidManifest to use the new icons
    update_manifest_icons()

def generate_launcher_icons(logo_path, config):
    """Generate launcher icons in various densities"""
    app_module = find_android_app_module()  # This will use cached result
    
    # Android launcher icon sizes (in pixels)
    icon_sizes = {
        'mdpi': 48,
        'hdpi': 72,
        'xhdpi': 96,
        'xxhdpi': 144,
        'xxxhdpi': 192
    }
    
    # Load the source logo
    try:
        source_image = Image.open(logo_path)
        print(f"📱 Generating launcher icons from: {logo_path}")
    except Exception as e:
        print(f"❌ Error loading logo: {e}")
        return
    
    # Convert to RGBA if needed
    if source_image.mode != 'RGBA':
        source_image = source_image.convert('RGBA')
    
    for density, size in icon_sizes.items():
        # Create mipmap directory
        mipmap_dir = app_module / f'src/main/res/mipmap-{density}'
        os.makedirs(mipmap_dir, exist_ok=True)
        
        # Generate square icon
        square_icon = create_square_icon(source_image, size)
        square_path = mipmap_dir / 'ic_launcher.webp'
        square_icon.save(square_path, 'WEBP', quality=90)
        
        # Generate round icon
        round_icon = create_round_icon(source_image, size)
        round_path = mipmap_dir / 'ic_launcher_round.webp'
        round_icon.save(round_path, 'WEBP', quality=90)
        
        # Generate foreground for adaptive icon
        foreground_icon = create_adaptive_foreground(source_image, size)
        foreground_path = mipmap_dir / 'ic_launcher_foreground.webp'
        foreground_icon.save(foreground_path, 'WEBP', quality=90)
        
        print(f"  ✓ Generated {density} icons ({size}x{size})")
    
    # Generate adaptive icon background
    generate_adaptive_background(config)
    
    # Generate adaptive icon XML
    generate_adaptive_icon_xml()

def create_square_icon(source_image, size):
    """Create a square launcher icon"""
    # Resize image to fit within the icon size with padding
    padding = int(size * 0.1)  # 10% padding
    content_size = size - (2 * padding)
    
    # Resize source image to content size
    resized = source_image.resize((content_size, content_size), Image.Resampling.LANCZOS)
    
    # Create new image with background
    icon = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    
    # Paste resized image in center
    offset = padding
    icon.paste(resized, (offset, offset), resized)
    
    return icon

def create_round_icon(source_image, size):
    """Create a round launcher icon"""
    # Create square icon first
    square_icon = create_square_icon(source_image, size)
    
    # Create circular mask
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    
    # Apply circular mask
    round_icon = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    round_icon.paste(square_icon, (0, 0))
    round_icon.putalpha(mask)
    
    return round_icon

def create_adaptive_foreground(source_image, size):
    """Create adaptive icon foreground"""
    # For adaptive icons, we need 108dp canvas with 72dp safe zone
    # The safe zone is centered, so we have 18dp padding on each side
    safe_zone_ratio = 72 / 108  # 0.667
    safe_zone_size = int(size * safe_zone_ratio)
    
    # Resize source to fit safe zone
    resized = source_image.resize((safe_zone_size, safe_zone_size), Image.Resampling.LANCZOS)
    
    # Create canvas and center the image
    foreground = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    offset = (size - safe_zone_size) // 2
    foreground.paste(resized, (offset, offset), resized)
    
    return foreground

def generate_adaptive_background(config):
    """Generate adaptive icon background"""
    app_module = find_android_app_module()  # This will use cached result
    
    # Use primary color as background
    branding = config["branding"]
    primary_color = branding.get("primary", "#6650a4")
    
    # Convert hex to RGB
    hex_color = primary_color.lstrip('#')
    rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    icon_sizes = {
        'mdpi': 48,
        'hdpi': 72,
        'xhdpi': 96,
        'xxhdpi': 144,
        'xxxhdpi': 192
    }
    
    for density, size in icon_sizes.items():
        mipmap_dir = app_module / f'src/main/res/mipmap-{density}'
        os.makedirs(mipmap_dir, exist_ok=True)
        
        # Create solid color background
        background = Image.new('RGB', (size, size), rgb_color)
        background_path = mipmap_dir / 'ic_launcher_background.webp'
        background.save(background_path, 'WEBP', quality=90)

def generate_adaptive_icon_xml():
    """Generate adaptive icon XML files"""
    app_module = find_android_app_module()  # This will use cached result

    # Create drawable-anydpi-v26 directory (adaptive icons require API 26+)
    drawable_dir = app_module / 'src/main/res/mipmap-anydpi-v26'
    os.makedirs(drawable_dir, exist_ok=True)
    
    # Generate ic_launcher.xml
    launcher_xml = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>'''
    
    with open(drawable_dir / 'ic_launcher.xml', 'w') as f:
        f.write(launcher_xml)
    
    # Generate ic_launcher_round.xml
    launcher_round_xml = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>'''
    
    with open(drawable_dir / 'ic_launcher_round.xml', 'w') as f:
        f.write(launcher_round_xml)
    
    print("✓ Generated adaptive icon XML files in drawable-v26")

def update_manifest_icons():
    """Update AndroidManifest.xml to use the generated icons"""
    manifest_path = get_app_source_path('src/main/AndroidManifest.xml')
    if not manifest_path.exists():
        print("⚠ AndroidManifest.xml not found")
        return
    
    with open(manifest_path, 'r') as f:
        content = f.read()
    
    # Update android:icon
    content = re.sub(
        r'android:icon="[^"]*"',
        'android:icon="@mipmap/ic_launcher"',
        content
    )
    
    # Update android:roundIcon
    content = re.sub(
        r'android:roundIcon="[^"]*"',
        'android:roundIcon="@mipmap/ic_launcher_round"',
        content
    )
    
    # If roundIcon doesn't exist, add it
    if 'android:roundIcon' not in content:
        content = re.sub(
            r'(android:icon="@mipmap/ic_launcher")',
            r'\1\n        android:roundIcon="@mipmap/ic_launcher_round"',
            content
        )
    
    with open(manifest_path, 'w') as f:
        f.write(content)
    
    print("✓ Updated AndroidManifest.xml with new icons")

def create_theme_xml(config):
    """Create or update theme.xml with brand colors"""
    theme_path = get_app_source_path('src/main/res/values/themes.xml')
    
    # Check if the project uses Compose primarily
    if uses_compose_theming():
        print("✓ Project uses Compose theming, skipping XML theme creation")
        return
    
    # Try to detect existing theme parent
    existing_parent = detect_existing_theme_parent()
    
    if existing_parent:
        print(f"✓ Using existing theme parent: {existing_parent}")
        parent_theme = existing_parent
    else:
        print("⚠ No existing theme found, using default Material3 parent")
        parent_theme = "Theme.Material3.DayNight"
    
    # Generate theme name from app name or slug
    theme_name = generate_theme_name(config)
    
    # Get colors
    branding = config["branding"]
    primary_color = branding.get("primary", "#6650a4")
    secondary_color = branding.get("secondary", "#625b71")
    background_color = branding.get("background", "#FFFBFE")
    
    theme_content = f'''<resources xmlns:tools="http://schemas.android.com/tools">
    <!-- Base application theme. -->
    <style name="{theme_name}" parent="{parent_theme}">
        <!-- Primary brand color. -->
        <item name="colorPrimary">{primary_color}</item>
        <item name="colorPrimaryVariant">{secondary_color}</item>
        <item name="colorOnPrimary">@color/white</item>
        <!-- Secondary brand color. -->
        <item name="colorSecondary">{secondary_color}</item>
        <item name="colorSecondaryVariant">{primary_color}</item>
        <item name="colorOnSecondary">@color/black</item>
        <!-- Status bar color. -->
        <item name="android:statusBarColor">?attr/colorPrimaryVariant</item>
        <!-- Customize your theme here. -->
        <item name="android:windowBackground">{background_color}</item>
    </style>
</resources>'''
    
    os.makedirs(theme_path.parent, exist_ok=True)
    with open(theme_path, 'w') as f:
        f.write(theme_content)
    print("✓ Created theme with brand colors")

def uses_compose_theming():
    """Check if the project primarily uses Compose theming"""
    app_module = find_android_app_module()
    
    # Check for Compose theme files
    compose_theme_files = find_compose_theme_files()
    if compose_theme_files:
        print(f"📱 Found {len(compose_theme_files)} Compose theme files")
        return True
    
    # Check build.gradle for Compose dependencies
    build_gradle_path = app_module / 'build.gradle.kts'
    if not build_gradle_path.exists():
        build_gradle_path = app_module / 'build.gradle'
    
    if build_gradle_path.exists():
        try:
            with open(build_gradle_path, 'r') as f:
                content = f.read()
            
            # Look for Compose BOM or Material3 dependencies
            if ('compose-bom' in content or 
                'material3' in content or
                'compose.material3' in content or
                'androidx.compose.material3' in content):
                print("📱 Found Compose dependencies in build.gradle")
                return True
                
        except Exception as e:
            print(f"⚠ Error reading build.gradle: {e}")
    
    return False

def detect_existing_theme_parent():
    """Detect the parent theme being used in existing themes.xml"""
    theme_path = get_app_source_path('src/main/res/values/themes.xml')
    
    if not theme_path.exists():
        return None
    
    try:
        with open(theme_path, 'r') as f:
            content = f.read()
        
        # Look for style definitions with parent attribute
        style_matches = re.findall(r'<style[^>]+name="[^"]*"[^>]+parent="([^"]+)"', content)
        
        if style_matches:
            # Return the first parent theme found
            parent = style_matches[0]
            print(f"📱 Found existing theme parent: {parent}")
            return parent
            
        # Also check for more complex style definitions
        multiline_matches = re.findall(r'<style[^>]*parent="([^"]+)"[^>]*>', content)
        if multiline_matches:
            parent = multiline_matches[0]
            print(f"📱 Found existing theme parent: {parent}")
            return parent
            
    except Exception as e:
        print(f"⚠ Error reading existing themes.xml: {e}")
    
    return None

def generate_theme_name(config):
    """Generate a theme name from config"""
    app_name = config["appName"].replace(' ', '').replace('-', '').replace('_', '')
    return f"Theme.{app_name}"

def main():
    # Check for command line arguments
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = 'flavor_config.json'  # Default fallback
    
    # Check if file exists
    if not Path(file_path).exists():
        print(f"❌ Configuration file not found: {file_path}")
        print("Usage: python apply-branding.py [config_file.json]")
        sys.exit(1)
    
    print("🎨 Applying branding configuration...")
    print(f"📄 Using config file: {file_path}")
    # print file content with json pretty for debugging
    with open(file_path, 'r') as f:
        content = f.read()
        print("📄 Config file content:")
        print(json.dumps(json.loads(content), indent=2))
    
    # Load configuration
    config = load_config(file_path)
    
    print(f"📱 Client: {config['clientName']}")
    print(f"📱 App Name: {config['appName']}")
    print(f"📦 Package: {config['packageName']}")
    
    # Display color information
    branding = config['branding']
    primary_color = branding.get('primary', 'N/A')
    secondary_color = branding.get('secondary', 'N/A')
    print(f"🎨 Primary Colors: {primary_color}, {secondary_color}")
    
    # Display all available colors
    print("\n🎨 Available Material Design 3 Colors:")
    color_fields = [
        ('primary', 'Primary brand color'),
        ('on_primary', 'Text/content color on primary'),
        ('secondary', 'Secondary brand color'),
        ('on_secondary', 'Text/content color on secondary'),
        ('tertiary', 'Tertiary accent color'),
        ('on_tertiary', 'Text/content color on tertiary'),
        ('background', 'Background color'),
        ('on_background', 'Text/content color on background'),
        ('surface', 'Surface color'),
        ('on_surface', 'Text/content color on surface')
    ]
    
    for field, description in color_fields:
        value = branding.get(field, 'Not provided')
        print(f"  • {field}: {value} ({description})")
    
    print()
    
    # Apply branding changes in the correct order
    # 1. First update package references everywhere
    update_package_name(config)
    restructure_source_directories(config)
    
    # 2. Then update content that depends on the new package structure
    update_app_name(config)
    update_colors(config)
    generate_app_icons(config)
    create_theme_xml(config)
    
    print("\n✅ Branding applied successfully!")

if __name__ == "__main__":
    main()
