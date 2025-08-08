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
from pathlib import Path

def load_config():
    """Load the flavor configuration from JSON file"""
    with open('flavor_config.json', 'r') as f:
        return json.load(f)

def update_app_name(config):
    """Update app name in strings.xml"""
    strings_path = Path('app/src/main/res/values/strings.xml')
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
    """Update colors in colors.xml"""
    colors_path = Path('app/src/main/res/values/colors.xml')
    
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
    print(f"✓ Updated colors: primary={config['branding']['primaryColor']}, secondary={config['branding']['secondaryColor']}")

def update_package_name(config):
    """Update package name in build.gradle and AndroidManifest.xml"""
    # Update build.gradle
    build_gradle_path = Path('app/build.gradle.kts')
    if not build_gradle_path.exists():
        build_gradle_path = Path('app/build.gradle')
    
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
    manifest_path = Path('app/src/main/AndroidManifest.xml')
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
    # Define source directories to process
    source_dirs = [
        'app/src/main/java',
        'app/src/main/kotlin',
        'app/src/test/java',
        'app/src/test/kotlin',
        'app/src/androidTest/java',
        'app/src/androidTest/kotlin'
    ]
    
    new_package = config["packageName"]
    new_package_path = new_package.replace('.', '/')
    
    for source_dir in source_dirs:
        source_path = Path(source_dir)
        if not source_path.exists():
            continue
            
        print(f"🔄 Processing {source_dir}...")
        
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
        if item.is_file() and item.suffix in ['.kt', '.java']:
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
    for file_path in old_package_dir.glob('*'):
        if file_path.is_file() and file_path.suffix in ['.kt', '.java']:
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
            
            # Remove old file
            file_path.unlink()
    
    # Remove old empty directories
    cleanup_empty_directories(old_package_dir)

def update_package_declaration(content, new_package):
    """Update package declaration in source files"""
    # Update package declaration
    pattern = r'^package\s+[a-zA-Z][a-zA-Z0-9_.]*'
    replacement = f'package {new_package}'
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

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
    
    # Import Pillow for image processing
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("⚠ Pillow not installed. Installing...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'Pillow'])
        from PIL import Image, ImageDraw
    
    # Generate launcher icons
    generate_launcher_icons(logo_path, config)
    
    # Update AndroidManifest to use the new icons
    update_manifest_icons(config)

def generate_launcher_icons(logo_path, config):
    """Generate launcher icons in various densities"""
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
        mipmap_dir = Path(f'app/src/main/res/mipmap-{density}')
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
    generate_adaptive_icon_xml(config)

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
        mipmap_dir = Path(f'app/src/main/res/mipmap-{density}')
        os.makedirs(mipmap_dir, exist_ok=True)
        
        # Create solid color background
        background = Image.new('RGB', (size, size), rgb_color)
        background_path = mipmap_dir / 'ic_launcher_background.webp'
        background.save(background_path, 'WEBP', quality=90)

def generate_adaptive_icon_xml(config):
    """Generate adaptive icon XML files"""
    # Create drawable directory
    drawable_dir = Path('app/src/main/res/drawable')
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
    
    print("✓ Generated adaptive icon XML files")

def update_manifest_icons(config):
    """Update AndroidManifest.xml to use the generated icons"""
    manifest_path = Path('app/src/main/AndroidManifest.xml')
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
    theme_path = Path('app/src/main/res/values/themes.xml')
    
    theme_content = f'''<resources xmlns:tools="http://schemas.android.com/tools">
    <!-- Base application theme. -->
    <style name="Theme.{config['slug'].replace('-', '').title()}" parent="Theme.MaterialComponents.DayNight.DarkActionBar">
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

def main():
    print("🎨 Applying branding configuration...")
    
    # Load configuration
    config = load_config()
    
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
    copy_logo(config)
    create_theme_xml(config)
    
    print("\n✅ Branding applied successfully!")

if __name__ == "__main__":
    main()
