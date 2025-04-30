#!/usr/bin/env python3
"""
install_dependencies.py - Cross-platform dependency installation script

This script installs dependencies based on the current platform, handling
platform-specific packages appropriately.
"""

import os
import sys
import platform
import subprocess

def install_dependencies():
    """Install dependencies based on the current platform."""
    # Base dependencies for all platforms
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install from the cross-platform requirements file
    if os.path.exists("requirements-cross-platform.txt"):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-cross-platform.txt"])
    else:
        # Fallback to the regular requirements file, skipping platform-specific packages
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"])
    
    # Install platform-specific packages
    if platform.system() == "Windows":
        print("Installing Windows-specific dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32==310"])
    
    print("Dependencies installed successfully!")

if __name__ == "__main__":
    install_dependencies()
