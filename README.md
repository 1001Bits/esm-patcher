# Fallout 4 ESM Patcher

## Description
The **Fallout 4 ESM Patcher** is a lightweight tool designed to make your Fallout 4 VR installation compatible with *Fallout: London* and other mods by patching the `Fallout4.esm` file to a pre-Next-Gen version. The Next-Gen update for Fallout 4 introduced changes to `Fallout4.esm` that can cause compatibility issues with VR mods, including *Fallout: London VR*. This tool automatically detects your `Fallout4.esm` version (based on file size) and applies the correct patch to ensure a smooth VR experience.

### Key Features
- **Automatic Detection**: Identifies the version of `Fallout4.esm` (323,025 KB or 322,806 KB variants) and applies the appropriate patch.
- **Backup Creation**: Creates a backup of your original `Fallout4.esm` before patching, ensuring you can revert if needed.
- **User-Friendly Interface**: Simple GUI for selecting your Fallout 4 VR Data directory, with optional command-line support for advanced users.
- **Fast and Lightweight**: Minimal footprint with no external dependencies required.

### Why You Need This
If you're playing *Fallout: London* in VR or using other mods that require a pre-Next-Gen `Fallout4.esm`, this tool is essential. It saves you from manually downgrading your game or hunting for compatible patches, making your modding experience hassle-free.

## Installation
1. **Download**: Grab the latest version from the Nexus Mods Files tab.
2. **Run the Tool**:
   - Launch `esm_downgrader.exe`.
   - Select your Fallout 4 VR Data directory (e.g., `C:\Program Files (x86)\Steam\steamapps\common\Fallout 4 VR\Data`).
   - Click "Patch" to apply the downgrade.
3. **Verify**: The tool will create a backup (`Fallout4.esm.backup`) and patch your `Fallout4.esm`. Check the log file (`downgrader.log`) for details.
4. **Optional (Manual Installation)**: For mod manager users, extract the archive to your mod directory and run the included `install.bat` script.

## Requirements
- Fallout 4 VR installed with `Fallout4.esm` in the Data directory.
- Approximately 350 MB of free disk space for the backup and patched files.

## Compatibility
- Compatible with Steam and GOG versions of Fallout 4 VR.
- Supports `Fallout4.esm` sizes of 330,777,465 bytes (323,025 KB) and 330,553,163 bytes (322,806 KB).
- Works with *Fallout: London VR* and other mods requiring pre-Next-Gen `Fallout4.esm`.

## Notes
- Always ensure you have a backup of your game files before patching.
- If your `Fallout4.esm` size doesn't match the supported versions, the tool will warn you and skip patching to prevent issues.
- For *Fallout: London VR* users, this downgrader is included in the full installer but is offered here as a standalone tool for flexibility.

## Credits
- Developed by [Your Name/Handle].
- Built using `xdelta3` for patching.
- Special thanks to the *Fallout: London* and VR modding communities for inspiration and support.

## Support
- Found a bug? Have a suggestion? Post in the Nexus Mods Comments tab.
- If you find this tool helpful, consider supporting its development at [Your Ko-fi/Patreon Link].

## Changelog
- **v1.0.0**: Initial release with support for 323,025 KB and 322,806 KB `Fallout4.esm` variants.
