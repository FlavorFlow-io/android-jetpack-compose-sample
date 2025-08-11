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
    
    # Create theme directory structure
    package_path = config["packageName"].replace('.', '/')
    theme_dir = main_source_dir / package_path / 'ui' / 'theme'
    os.makedirs(theme_dir, exist_ok=True)
    
    # Create Color.kt file
    create_compose_color_file(theme_dir, config)
    
    # Create Theme.kt file
    create_compose_theme_file(theme_dir, config)
    
    # Create Type.kt file (Typography)
    create_compose_typography_file(theme_dir, config)
    
    print(f"✓ Created Compose theme files in: {theme_dir}")

def create_compose_color_file(theme_dir, config):
    """Create Color.kt file for Compose"""
    primary_color = hex_to_compose_color(config["branding"]["primaryColor"])
    secondary_color = hex_to_compose_color(config["branding"]["secondaryColor"])
    background_color = hex_to_compose_color(config["branding"]["backgroundColor"])
    
    color_content = f'''package {config["packageName"]}.ui.theme

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

def create_compose_theme_file(theme_dir, config):
    """Create Theme.kt file for Compose"""
    app_name = config["appName"].replace(' ', '')
    
    theme_content = f'''package {config["packageName"]}.ui.theme

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
    primary = LightPrimary,
    secondary = LightSecondary,
    background = LightBackground,
    // Add more colors as needed
)

private val DarkColorScheme = darkColorScheme(
    primary = DarkPrimary,
    secondary = DarkSecondary,
    background = DarkBackground,
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

def create_compose_typography_file(theme_dir, config):
    """Create Type.kt file for Compose Typography"""
    typography_content = f'''package {config["packageName"]}.ui.theme

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
        
        with open(build_gradle_path, 'w') as f:
            f.write(content)
        print(f"✓ Updated package name in build.gradle to: {config['packageName']}")
    
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
    
    for source_dir in source_dirs:
        source_path = app_module / source_dir
        if not source_path.exists():
            continue
            
        print(f"🔄 Processing {source_path}...")
        
        # Find existing package structure
        existing_packages = find_existing_packages(source_path)
        
        if existing_packages:
            # Move files from old package structure to new one
            for old_package_dir in existing_packages:
                move_source_files(old_package_dir, source_path / new_package_path, new_package)
        else:
            # No existing packages found, create the new structure
            new_package_dir = source_path / new_package_path
            os.makedirs(new_package_dir, exist_ok=True)
            print(f"✓ Created new package directory: {new_package_dir}")

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
    """Move source files and update package declarations"""
    if not old_package_dir.exists():
        return
    
    # Create new package directory
    os.makedirs(new_package_dir, exist_ok=True)
    
    # Move all source files
    moved_files = []
    for file_path in old_package_dir.glob('*'):
        if file_path.is_file() and file_path.suffix in SOURCE_EXTENSIONS:
            # Read file content
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Update package declaration
            content = update_package_declaration(content, new_package)
            
            # Write to new location
            new_file_path = new_package_dir / file_path.name
            with open(new_file_path, 'w') as f:
                f.write(content)
            
            print(f"  ✓ Moved {file_path.name} to {new_package_dir}")
            moved_files.append(file_path.name)
            
            # Remove old file
            file_path.unlink()
    
    if moved_files:
        # Get the root of the old package structure to clean up
        old_package_root = get_old_package_root(old_package_dir)
        
        # Remove old empty directories starting from the deepest level
        cleanup_old_package_structure(old_package_root)
        
        print(f"  🗑️ Cleaned up old package structure starting from {old_package_root}")

def update_package_declaration(content, new_package):
    """Update package declaration in source files"""
    # Update package declaration
    pattern = r'^package\s+[a-zA-Z][a-zA-Z0-9_.]*'
    replacement = f'package {new_package}'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
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
    
    # Create drawable-v26 directory (adaptive icons require API 26+)
    drawable_dir = app_module / 'src/main/res/drawable-v26'
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
    
    # Apply branding changes
    update_app_name(config)
    update_colors(config)
    update_package_name(config)
    restructure_source_directories(config)
    generate_app_icons(config)
    create_theme_xml(config)
    
    print("\n✅ Branding applied successfully!")

if __name__ == "__main__":
    main()
