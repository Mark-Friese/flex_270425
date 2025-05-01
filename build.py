"""
build.py - PyInstaller script for building the Flexibility Analysis System desktop application

This script uses PyInstaller to create a standalone executable for the application.
"""

import os
import sys
import shutil
import platform
from pathlib import Path

def clean_build_directories():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"Cleaning {dir_path}...")
            shutil.rmtree(dir_path)

def build_application():
    """Build the application using PyInstaller"""
    # Determine platform-specific options
    is_windows = platform.system() == 'Windows'
    
    # Base command
    cmd = [
        'pyinstaller',
        '--name=FlexibilityAnalysisSystem',
        '--add-data=ui{0}ui'.format(os.pathsep),
        '--add-data=config.yaml{0}.'.format(os.pathsep),
        '--add-data=config_with_competitions.yaml{0}.'.format(os.pathsep),
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=matplotlib',
        '--hidden-import=matplotlib.backends.backend_agg',
        '--hidden-import=yaml',
    ]
    
    # Add platform-specific options
    if is_windows:
        cmd.extend([
            '--windowed',      # Don't show console window on Windows
            '--icon=ui/favicon.ico' if Path('ui/favicon.ico').exists() else '',
        ])
    
    # Specify the main script
    cmd.append('app.py')
    
    # Filter out empty strings
    cmd = [c for c in cmd if c]
    
    # Print the command
    print("Running PyInstaller with:", ' '.join(cmd))
    
    # Execute the command
    import PyInstaller.__main__
    PyInstaller.__main__.run(cmd)

def post_build_processing():
    """Perform post-build actions"""
    # Create a data directory in the distribution
    dist_dir = Path('dist/FlexibilityAnalysisSystem')
    data_dir = dist_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # Copy sample data if it exists
    source_data_dir = Path('data')
    if source_data_dir.exists():
        for file in source_data_dir.glob('**/*'):
            if file.is_file():
                relative_path = file.relative_to(source_data_dir)
                target_path = data_dir / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, target_path)
                print(f"Copied {file} to {target_path}")
    
    # Create output directory
    output_dir = dist_dir / 'output'
    output_dir.mkdir(exist_ok=True)
    
    # Copy schema file if it exists
    schema_file = Path('flexibility_competition_schema.json')
    if schema_file.exists():
        shutil.copy2(schema_file, dist_dir)
        print(f"Copied {schema_file} to {dist_dir}")
    
    print(f"Build completed. Output directory: {dist_dir.absolute()}")

def copy_documentation():
    """Copy the built documentation into the distribution"""
    site_dir = Path('site')
    if not site_dir.exists():
        print("Documentation site directory not found. Skipping documentation.")
        return
    
    dist_dir = Path('dist/FlexibilityAnalysisSystem')
    docs_dir = dist_dir / 'ui' / 'site'
    
    # Create docs directory if it doesn't exist
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all contents of site directory to docs directory
    print(f"Copying documentation from {site_dir} to {docs_dir}...")
    try:
        import shutil
        if docs_dir.exists():
            # Clear existing documentation files
            for item in docs_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        
        # Copy all contents
        for item in site_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, docs_dir / item.name)
            else:
                shutil.copy2(item, docs_dir / item.name)
        
        print(f"Documentation copied successfully.")
    except Exception as e:
        print(f"Error copying documentation: {str(e)}")

def main():
    """Main build process"""
    print("Starting build process for Flexibility Analysis System...")
    
    # Clean previous build
    clean_build_directories()
    
    # Build the application
    build_application()
    
    # Post-build processing
    post_build_processing()
    
    # Copy documentation if available
    copy_documentation()
    
    print("Build complete!")

if __name__ == "__main__":
    main()
