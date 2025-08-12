#!/usr/bin/env python3
"""
FlavorFlow Branding Application Script

This script applies branding configuration to an Android project based on
the flavor configuration JSON file.
"""

import json
import os
import re
import shutil
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
    
    # Create colors.xml content
    colors_content = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="primary_color">{config["branding"]["primaryColor"]}</color>
    <color name="secondary_color">{config["branding"]["secondaryColor"]}</color>
    <color name="background_color">{config["branding"]["backgroundColor"]}</color>
    
    <!-- Material Design Colors -->
    <color name="purple_200">{config["branding"]["primaryColor"]}</color>
    <color name="purple_500">{config["branding"]["primaryColor"]}</color>
    <color name="purple_700">{config["branding"]["secondaryColor"]}</color>
    <color name="teal_200">{config["branding"]["secondaryColor"]}</color>
    <color name="teal_700">{config["branding"]["secondaryColor"]}</color>
    <color name="black">#FF000000</color>
    <color name="white">#FFFFFFFF</color>
</resources>'''
    
    os.makedirs(colors_path.parent, exist_ok=True)
    with open(colors_path, 'w') as f:
        f.write(colors_content)
    print(f"✓ Updated XML colors: primary={config['branding']['primaryColor']}, secondary={config['branding']['secondaryColor']}")

def update_compose_theme(config):
    """Update Compose theme files"""
    # Look for existing Compose theme files
    theme_files = find_compose_theme_files()
    
    if theme_files:
        for theme_file in theme_files:
            update_existing_compose_theme(theme_file, config)
    else:
        # Create new Compose theme files
        create_compose_theme_files(config)

def find_compose_theme_files():
    """Find existing Compose theme files"""
    theme_files = []
    app_module = find_android_app_module()  # This will use cached result
    
    # Common paths for Compose theme files relative to app module
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
                    if any(keyword in file.name.lower() for keyword in ['color', 'theme']):
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
    with open(theme_file, 'r') as f:
        content = f.read()
    
    # Update color definitions based on common patterns
    content = update_compose_colors(content, config)
    
    with open(theme_file, 'w') as f:
        f.write(content)
    
    print(f"✓ Updated Compose theme file: {theme_file}")

def update_compose_colors(content, config):
    """Update color definitions in Compose theme content"""
    primary_color = config["branding"]["primaryColor"]
    secondary_color = config["branding"]["secondaryColor"]
    background_color = config["branding"]["backgroundColor"]
    
    # Convert hex to Compose Color format
    primary_compose = hex_to_compose_color(primary_color)
    secondary_compose = hex_to_compose_color(secondary_color)
    background_compose = hex_to_compose_color(background_color)
    
    # Update various color patterns
    patterns = [
        # Standard color definitions
        (r'val\s+Primary\s*=\s*Color\([^)]+\)', f'val Primary = Color({primary_compose})'),
        (r'val\s+Secondary\s*=\s*Color\([^)]+\)', f'val Secondary = Color({secondary_compose})'),
        (r'val\s+Background\s*=\s*Color\([^)]+\)', f'val Background = Color({background_compose})'),
        
        # Material3 color scheme patterns
        (r'primary\s*=\s*Color\([^)]+\)', f'primary = Color({primary_compose})'),
        (r'secondary\s*=\s*Color\([^)]+\)', f'secondary = Color({secondary_compose})'),
        (r'background\s*=\s*Color\([^)]+\)', f'background = Color({background_compose})'),
        
        # Custom color definitions
        (r'val\s+primaryColor\s*=\s*Color\([^)]+\)', f'val primaryColor = Color({primary_compose})'),
        (r'val\s+secondaryColor\s*=\s*Color\([^)]+\)', f'val secondaryColor = Color({secondary_compose})'),
        (r'val\s+backgroundColor\s*=\s*Color\([^)]+\)', f'val backgroundColor = Color({background_compose})'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
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
    
    # Create Theme.kt file
    create_compose_theme_file(theme_dir, config, package_with_subdir)
    
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
    
    primary_color = hex_to_compose_color(config["branding"]["primaryColor"])
    secondary_color = hex_to_compose_color(config["branding"]["secondaryColor"])
    background_color = hex_to_compose_color(config["branding"]["backgroundColor"])
    
    color_content = f'''package {package_name}

import androidx.compose.ui.graphics.Color

val Primary = Color({primary_color})
val Secondary = Color({secondary_color})
val Background = Color({background_color})

// Light theme colors
val LightPrimary = Color({primary_color})
val LightSecondary = Color({secondary_color})
val LightBackground = Color({background_color})

// Dark theme colors (you can customize these)
val DarkPrimary = Color({primary_color})
val DarkSecondary = Color({secondary_color})
val DarkBackground = Color(0xFF121212)

// Additional brand colors
val BrandPrimary = Color({primary_color})
val BrandSecondary = Color({secondary_color})
val BrandBackground = Color({background_color})
'''
    
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
    
    primary_color = hex_to_compose_color(config["branding"]["primaryColor"])
    secondary_color = hex_to_compose_color(config["branding"]["secondaryColor"])
    background_color = hex_to_compose_color(config["branding"]["backgroundColor"])
    
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColorScheme = lightColorScheme(
    primary = Color({primary_color}),
    secondary = Color({secondary_color}),
    background = Color({background_color}),
    // Add more colors as needed
)

private val DarkColorScheme = darkColorScheme(
    primary = Color({primary_color}),
    secondary = Color({secondary_color}),
    background = Color(0xFF121212),
    // Add more colors as needed
)

@Composable
fun {app_name}Theme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
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
        typography = Typography,
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
    logo_path = Path(config["branding"]["logoPath"])
    if not logo_path.exists():
        print(f"⚠ Logo file not found: {logo_path}")
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
    primary_color = config["branding"]["primaryColor"]
    
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
    
    theme_content = f'''<resources xmlns:tools="http://schemas.android.com/tools">
    <!-- Base application theme. -->
    <style name="{theme_name}" parent="{parent_theme}">
        <!-- Primary brand color. -->
        <item name="colorPrimary">{config["branding"]["primaryColor"]}</item>
        <item name="colorPrimaryVariant">{config["branding"]["secondaryColor"]}</item>
        <item name="colorOnPrimary">@color/white</item>
        <!-- Secondary brand color. -->
        <item name="colorSecondary">{config["branding"]["secondaryColor"]}</item>
        <item name="colorSecondaryVariant">{config["branding"]["primaryColor"]}</item>
        <item name="colorOnSecondary">@color/black</item>
        <!-- Status bar color. -->
        <item name="android:statusBarColor">?attr/colorPrimaryVariant</item>
        <!-- Customize your theme here. -->
        <item name="android:windowBackground">{config["branding"]["backgroundColor"]}</item>
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
    if 'slug' in config and config['slug']:
        # Use slug if available
        theme_name = config['slug'].replace('-', '').replace('_', '').title()
        return f"Theme.{theme_name}"
    else:
        # Use app name as fallback
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
    
    # Load configuration
    config = load_config(file_path)
    
    print(f"📱 Client: {config['clientName']}")
    print(f"📱 App Name: {config['appName']}")
    print(f"📦 Package: {config['packageName']}")
    print(f"🎨 Colors: {config['branding']['primaryColor']}, {config['branding']['secondaryColor']}")
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
