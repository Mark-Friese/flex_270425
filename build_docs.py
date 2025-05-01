#!/usr/bin/env python3
"""
build_docs.py - Build and copy documentation for the Flexibility Analysis System

This script builds the mkdocs documentation and copies it to the appropriate
location for the desktop application.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_docs():
    """Build documentation using mkdocs."""
    print("Building documentation with mkdocs...")
    try:
        subprocess.run(["mkdocs", "build"], check=True)
        print("Documentation built successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error building documentation: {e}")
        return False
    except FileNotFoundError:
        print("Error: 'mkdocs' command not found. Please ensure mkdocs is installed.")
        print("You can install it with: pip install mkdocs mkdocs-material")
        return False

def copy_docs_to_app():
    """Copy built documentation to the app's UI directory."""
    site_dir = Path("site")
    app_docs_dir = Path("ui") / "site"
    
    if not site_dir.exists():
        print(f"Error: Built documentation not found at {site_dir}")
        return False
    
    print(f"Copying documentation from {site_dir} to {app_docs_dir}...")
    
    # Create app docs directory if it doesn't exist
    app_docs_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Clear existing documentation files
        if app_docs_dir.exists():
            for item in app_docs_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        
        # Copy all contents
        for item in site_dir.iterdir():
            if item.is_dir():
                shutil.copytree(item, app_docs_dir / item.name)
            else:
                shutil.copy2(item, app_docs_dir / item.name)
        
        print("Documentation copied successfully to app directory.")
        return True
    except Exception as e:
        print(f"Error copying documentation: {e}")
        return False

def main():
    """Main function"""
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    print("Starting documentation build process...")
    
    # Build the documentation
    if not build_docs():
        print("Documentation build failed. Exiting.")
        sys.exit(1)
    
    # Copy the documentation to the app
    if not copy_docs_to_app():
        print("Documentation copy failed. Exiting.")
        sys.exit(1)
    
    print("Documentation build and copy completed successfully!")

if __name__ == "__main__":
    main()
