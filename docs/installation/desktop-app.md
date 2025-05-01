# Desktop Application Installation

This guide covers installation of the Flexibility Analysis System desktop application, which provides a user-friendly graphical interface for the system.

## Pre-built Installers

The easiest way to install the desktop application is to use a pre-built installer.

### Windows Installation

1. Download the latest `FlexibilityAnalysisSystem-Setup.exe` from the [releases page](https://github.com/yourusername/flex_270425/releases)
2. Run the installer and follow the on-screen instructions
3. The application will be installed and a desktop shortcut will be created
4. Launch the application from the Start menu or desktop shortcut

### macOS Installation

1. Download the latest `FlexibilityAnalysisSystem.dmg` from the [releases page](https://github.com/yourusername/flex_270425/releases)
2. Open the DMG file
3. Drag the FlexibilityAnalysisSystem icon to the Applications folder
4. Launch the application from the Applications folder or Launchpad

### Linux Installation

1. Download the latest `FlexibilityAnalysisSystem.AppImage` from the [releases page](https://github.com/yourusername/flex_270425/releases)
2. Make the AppImage executable:
   ```bash
   chmod +x FlexibilityAnalysisSystem.AppImage
   ```
3. Run the application:
   ```bash
   ./FlexibilityAnalysisSystem.AppImage
   ```

## Running from Source

If you prefer to run the application directly from source code:

1. Ensure you have all prerequisites installed:
   ```bash
   pip install -r packaging_requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

## Building from Source

You can build the application from source to create a standalone executable.

### Prerequisites

Ensure you have the required dependencies installed:

```bash
pip install -r packaging_requirements.txt
```

### Building Process

1. Run the build script:
   ```bash
   python build.py
   ```

2. The built application will be available in the `dist` directory:
   - Windows: `dist/FlexibilityAnalysisSystem/FlexibilityAnalysisSystem.exe`
   - macOS: `dist/FlexibilityAnalysisSystem.app`
   - Linux: `dist/FlexibilityAnalysisSystem/FlexibilityAnalysisSystem`

### Creating Installers

#### Windows Installer

1. Install NSIS (Nullsoft Scriptable Install System)
2. Run the packaging script:
   ```bash
   python package_windows.py
   ```
3. The installer will be created in the `dist` directory

#### macOS DMG

1. Ensure you have `create-dmg` installed:
   ```bash
   brew install create-dmg
   ```
2. Run the packaging script:
   ```bash
   python package_macos.py
   ```
3. The DMG will be created in the `dist` directory

#### Linux AppImage

1. Ensure you have `appimagetool` installed
2. Run the packaging script:
   ```bash
   python package_linux.py
   ```
3. The AppImage will be created in the `dist` directory

## Application Structure

The built application includes:

- The main executable
- Python runtime
- All required dependencies
- Default configuration files
- Sample data (in the `data` directory)
- Documentation (in the `docs` directory)

## First Launch

When you first launch the application:

1. You'll be prompted to select or create a configuration file
2. The default output directory will be set to a user-accessible location
3. You'll be presented with a list of example substations from the sample data

## Troubleshooting

### Missing Dependencies

If you encounter missing dependency errors when running from source:
```bash
pip install -r requirements.txt
pip install -r packaging_requirements.txt
```

### Application Won't Start

On Windows, ensure you have the Visual C++ Redistributable installed. The installer should handle this automatically, but you can download it manually from the Microsoft website if needed.

On Linux, ensure you have the required system libraries:
```bash
# For Debian/Ubuntu
sudo apt-get install libgtk-3-0 libwebkit2gtk-4.0-37

# For Fedora/RHEL
sudo dnf install gtk3 webkit2gtk3
```

### Data Loading Issues

If you encounter issues loading data:

1. Check that your data files are in the expected format (CSV or Parquet)
2. Ensure the files are in the correct location as specified in your configuration
3. Check the application logs for specific error messages

## Updating

To update the application:

1. Download the latest installer from the releases page
2. Run the installer (it will automatically uninstall the previous version)
3. Your configurations and output data will be preserved during the update