#!/usr/bin/env python3
"""
Fallout 4 ESM Patcher
Version: 1.0.0
Author: [Your Name]
Description: Patches Next-Gen Fallout4.esm files for mod compatibility

This tool applies xdelta3 patches to convert Next-Gen Fallout4.esm files
to versions compatible with Fallout 4 VR, Fallout: London, and other mods.
"""

import os
import sys
import shutil
import subprocess
import tempfile
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import Optional, Tuple
import logging
from datetime import datetime

# Configure logging
log_filename = f"esm_patcher_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ESMPatcher:
    """Main patcher class for Fallout4.esm files"""
    
    # Known ESM sizes that need patching (exact byte counts)
    PATCH_MAPPINGS = {
        330777465: {  # Exactly 330,777,465 bytes
            "patch": "fallout4_323025.xdelta",
            "description": "323,025 KB variant",
            "md5": "a5c13fb8c0e2e9c7c0c8e6f9d4b5a3e2"  # Add actual MD5 if known
        },
        330553163: {  # Exactly 330,553,163 bytes
            "patch": "fallout4_322806.xdelta",
            "description": "322,806 KB variant",
            "md5": "b7d24fa9e1d3c8b6a4f5e7c9d2a1b3c4"  # Add actual MD5 if known
        }
    }
    
    # Known compatible ESM sizes (don't need patching)
    COMPATIBLE_SIZES = {
        330745373: "Already compatible (315.42 MB) - No patching needed",
        61741779: "Patched/compatible version (58.9 MB)",
        61598851: "Patched/compatible version (58.7 MB)",
    }
    
    def __init__(self):
        """Initialize the patcher"""
        self.assets_dir = self.get_assets_directory()
        self.xdelta_path = os.path.join(self.assets_dir, "xdelta3.exe")
        self.current_esm_path = None
        self.backup_created = False
        
    def get_assets_directory(self) -> str:
        """Get the assets directory path"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return os.path.join(sys._MEIPASS, "assets")
        else:
            # Running as script
            return os.path.join(os.path.dirname(__file__), "assets")
    
    def verify_dependencies(self) -> Tuple[bool, str]:
        """Verify all required files are present"""
        missing_files = []
        
        # Check xdelta3.exe
        if not os.path.exists(self.xdelta_path):
            missing_files.append("xdelta3.exe")
        
        # Check patch files
        for patch_info in self.PATCH_MAPPINGS.values():
            patch_path = os.path.join(self.assets_dir, patch_info["patch"])
            if not os.path.exists(patch_path):
                missing_files.append(patch_info["patch"])
        
        if missing_files:
            return False, f"Missing required files: {', '.join(missing_files)}"
        
        return True, "All dependencies verified"
    
    def get_file_info(self, file_path: str) -> dict:
        """Get detailed information about a file"""
        if not os.path.exists(file_path):
            return {"exists": False}
        
        file_size = os.path.getsize(file_path)
        
        # Calculate MD5 hash
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        
        return {
            "exists": True,
            "size": file_size,
            "size_mb": file_size / (1024 * 1024),
            "md5": md5_hash.hexdigest(),
            "path": file_path
        }
    
    def identify_esm_version(self, esm_path: str) -> Tuple[bool, str, Optional[dict]]:
        """Identify if ESM needs patching and which patch to use"""
        file_info = self.get_file_info(esm_path)
        
        if not file_info["exists"]:
            return False, "File does not exist", None
        
        file_size = file_info["size"]
        
        # Check if this is a known patchable size
        if file_size in self.PATCH_MAPPINGS:
            patch_info = self.PATCH_MAPPINGS[file_size]
            return True, f"Next-Gen ESM detected ({patch_info['description']})", patch_info
        
        # Check if it's already patched (different known sizes)
        known_patched_sizes = [
            (61741779, "VR-compatible version (58.9 MB)"),
            (61598851, "VR-compatible version (58.7 MB)"),
        ]
        
        for size, description in known_patched_sizes:
            if abs(file_size - size) < 1000:  # Within 1KB tolerance
                return False, f"Already patched: {description}", None
        
        # Unknown size
        return False, f"Unknown ESM version (size: {file_size:,} bytes)", None
    
    def create_backup(self, esm_path: str) -> Tuple[bool, str]:
        """Create a backup of the ESM file"""
        try:
            backup_path = esm_path + ".backup"
            
            # Check if backup already exists
            if os.path.exists(backup_path):
                response = messagebox.askyesno(
                    "Backup Exists",
                    f"A backup already exists at:\n{backup_path}\n\nOverwrite it?"
                )
                if not response:
                    return False, "Backup cancelled by user"
            
            logging.info(f"Creating backup: {backup_path}")
            shutil.copy2(esm_path, backup_path)
            self.backup_created = True
            
            return True, backup_path
            
        except Exception as e:
            logging.error(f"Failed to create backup: {e}")
            return False, str(e)
    
    def apply_patch(self, esm_path: str, patch_info: dict, progress_callback=None) -> Tuple[bool, str]:
        """Apply the xdelta3 patch to the ESM file"""
        try:
            patch_path = os.path.join(self.assets_dir, patch_info["patch"])
            temp_output = esm_path + ".patched"
            
            # Build xdelta3 command
            cmd = [
                self.xdelta_path,
                "-f",  # Force overwrite
                "-d",  # Decode
                "-s", esm_path,  # Source file
                patch_path,  # Patch file
                temp_output  # Output file
            ]
            
            logging.info(f"Running command: {' '.join(cmd)}")
            
            if progress_callback:
                progress_callback(30, "Applying patch...")
            
            # Run xdelta3
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                error_msg = f"xdelta3 failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nError: {result.stderr}"
                logging.error(error_msg)
                return False, error_msg
            
            if progress_callback:
                progress_callback(70, "Verifying patched file...")
            
            # Verify the patched file exists and has reasonable size
            if not os.path.exists(temp_output):
                return False, "Patched file was not created"
            
            patched_size = os.path.getsize(temp_output)
            if patched_size < 50000000:  # Less than 50MB is definitely wrong
                os.remove(temp_output)
                return False, f"Patched file is too small ({patched_size} bytes)"
            
            if progress_callback:
                progress_callback(90, "Replacing original file...")
            
            # Replace original with patched version
            os.remove(esm_path)
            os.rename(temp_output, esm_path)
            
            logging.info(f"Patch applied successfully. New size: {patched_size:,} bytes")
            
            return True, f"Patch applied successfully!\nNew file size: {patched_size:,} bytes ({patched_size/(1024*1024):.2f} MB)"
            
        except subprocess.TimeoutExpired:
            if os.path.exists(temp_output):
                os.remove(temp_output)
            return False, "Patching process timed out"
            
        except Exception as e:
            if os.path.exists(temp_output):
                os.remove(temp_output)
            logging.error(f"Error applying patch: {e}")
            return False, str(e)
    
    def restore_backup(self, esm_path: str) -> Tuple[bool, str]:
        """Restore the ESM file from backup"""
        backup_path = esm_path + ".backup"
        
        if not os.path.exists(backup_path):
            return False, "No backup file found"
        
        try:
            if os.path.exists(esm_path):
                os.remove(esm_path)
            shutil.copy2(backup_path, esm_path)
            logging.info(f"Restored from backup: {backup_path}")
            return True, "Successfully restored from backup"
        except Exception as e:
            logging.error(f"Failed to restore backup: {e}")
            return False, str(e)


class PatcherGUI:
    """GUI for the ESM Patcher"""
    
    def __init__(self):
        self.patcher = ESMPatcher()
        self.selected_file = None
        self.patch_info = None
        
        # Setup main window
        self.root = tk.Tk()
        self.root.title("Fallout 4 ESM Patcher v1.0")
        self.root.geometry("600x550")  # Increased height from 500 to 550
        self.root.resizable(False, False)
        
        # Set window icon if available
        try:
            icon_path = os.path.join(self.patcher.assets_dir, "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        self.setup_ui()
        
        # Verify dependencies on startup
        deps_ok, deps_msg = self.patcher.verify_dependencies()
        if not deps_ok:
            messagebox.showerror("Missing Dependencies", deps_msg)
            self.root.destroy()
            return
    
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=100)  # Increased height from 80 to 100
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="Fallout 4 ESM Patcher",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(pady=(20, 5))  # Adjusted padding
        
        tk.Label(
            title_frame,
            text="Patch Next-Gen ESM files for mod compatibility",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="#ecf0f1"
        ).pack(pady=(0, 10))  # Added bottom padding
        
        # Main content with adjusted padding
        main_frame = tk.Frame(self.root, padx=20, pady=15)  # Reduced vertical padding from 20 to 15
        main_frame.pack(fill="both", expand=True)
        
        # File selection
        tk.Label(main_frame, text="Select Fallout 4/Fallout 4 VR game folder:", font=("Arial", 12)).pack(anchor="w")
        
        file_frame = tk.Frame(main_frame)
        file_frame.pack(fill="x", pady=(5, 15))
        
        self.file_entry = tk.Entry(file_frame, font=("Arial", 10))
        self.file_entry.pack(side="left", fill="x", expand=True)
        
        tk.Button(
            file_frame,
            text="Browse Folder",
            command=self.browse_folder,
            width=12
        ).pack(side="right", padx=(5, 0))
        
        # Auto-detect button
        tk.Button(
            main_frame,
            text="Auto-Detect Fallout 4 Installations",
            command=self.auto_detect,
            width=30
        ).pack(pady=5)
        
        # Status display with adjusted height
        tk.Label(main_frame, text="File Status:", font=("Arial", 12)).pack(anchor="w", pady=(10, 5))  # Reduced top padding
        
        self.status_text = tk.Text(
            main_frame,
            height=7,  # Reduced from 8 to 7 lines
            font=("Courier", 9),
            bg="#f8f9fa",
            relief="groove",
            borderwidth=2
        )
        self.status_text.pack(fill="both", expand=True)
        
        # Progress bar
        self.progress_var = tk.IntVar()
        self.progress = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress.pack(fill="x", pady=(10, 5))
        
        self.progress_label = tk.Label(main_frame, text="", font=("Arial", 9))
        self.progress_label.pack()
        
        # Action buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(15, 10))  # Added bottom padding
        
        self.patch_button = tk.Button(
            button_frame,
            text="Apply Patch",
            command=self.apply_patch,
            state="disabled",
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=8,  # Increased padding
            height=1  # Explicit height
        )
        self.patch_button.pack(side="left", padx=5)
        
        self.restore_button = tk.Button(
            button_frame,
            text="Restore Backup",
            command=self.restore_backup,
            state="disabled",
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10),
            padx=15,
            pady=8,  # Increased padding
            height=1  # Explicit height
        )
        self.restore_button.pack(side="left", padx=5)
        
        # Help button
        tk.Button(
            button_frame,
            text="Help",
            command=self.show_help,
            font=("Arial", 10),
            padx=15,
            pady=8,  # Increased padding
            height=1  # Explicit height
        ).pack(side="left", padx=5)
    
    def browse_folder(self):
        """Browse for game folder and auto-detect Fallout4.esm"""
        folder_path = filedialog.askdirectory(
            title="Select Fallout 4 installation folder"
        )
        
        if folder_path:
            # Look for Fallout4.esm in different possible locations
            esm_found = False
            esm_path = None
            
            # Check patterns: root folder, Data subfolder
            search_locations = [
                os.path.join(folder_path, "Fallout4.esm"),
                os.path.join(folder_path, "Data", "Fallout4.esm"),
                os.path.join(folder_path, "data", "Fallout4.esm"),  # Case variation
            ]
            
            for location in search_locations:
                if os.path.exists(location):
                    esm_path = location
                    esm_found = True
                    break
            
            if esm_found:
                self.file_entry.delete(0, tk.END)
                self.file_entry.insert(0, esm_path)
                self.analyze_file(esm_path)
            else:
                messagebox.showwarning(
                    "ESM Not Found",
                    f"Fallout4.esm not found in:\n{folder_path}\n\n"
                    "Please select the Fallout 4 installation folder\n"
                    "(the folder containing Fallout4.exe or the Data folder)"
                )
    
    def browse_file(self):
        """Legacy browse for ESM file directly (kept for compatibility)"""
        file_path = filedialog.askopenfilename(
            title="Select Fallout4.esm",
            filetypes=[("ESM Files", "*.esm"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
            self.analyze_file(file_path)
    
    def auto_detect(self):
        """Auto-detect Fallout 4 installations"""
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, "Searching for Fallout 4 installations...\n\n")
        self.root.update()
        
        search_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Fallout 4",
            r"C:\Program Files (x86)\Steam\steamapps\common\Fallout 4 VR",
            r"C:\Games\Fallout 4",
            r"C:\Games\Fallout 4 VR",
            r"D:\Steam\steamapps\common\Fallout 4",
            r"D:\Steam\steamapps\common\Fallout 4 VR",
            r"D:\SteamLibrary\steamapps\common\Fallout 4",
            r"D:\SteamLibrary\steamapps\common\Fallout 4 VR",
            r"C:\GOG Games\Fallout 4",
            r"C:\Program Files (x86)\GOG Galaxy\Games\Fallout 4",
        ]
        
        found_files = []
        
        for base_path in search_paths:
            # Check both root and Data subfolder
            for sub_path in ["", "Data"]:
                full_path = os.path.join(base_path, sub_path) if sub_path else base_path
                esm_path = os.path.join(full_path, "Fallout4.esm")
                
                if os.path.exists(esm_path):
                    found_files.append(esm_path)
                    self.status_text.insert(tk.END, f"Found: {esm_path}\n")
        
        if found_files:
            self.status_text.insert(tk.END, f"\nFound {len(found_files)} installation(s)\n")
            if len(found_files) == 1:
                self.file_entry.delete(0, tk.END)
                self.file_entry.insert(0, found_files[0])
                self.analyze_file(found_files[0])
            else:
                self.status_text.insert(tk.END, "\nMultiple installations found. Analyzing first one...")
                self.file_entry.delete(0, tk.END)
                self.file_entry.insert(0, found_files[0])
                self.analyze_file(found_files[0])
        else:
            self.status_text.insert(tk.END, "\nNo Fallout 4 installations found.\nPlease browse manually using 'Browse Folder'.")
    
    def analyze_file(self, file_path: str):
        """Analyze the selected ESM file"""
        self.status_text.delete(1.0, tk.END)
        self.selected_file = file_path
        
        # Get file info
        file_info = self.patcher.get_file_info(file_path)
        
        if not file_info["exists"]:
            self.status_text.insert(tk.END, "ERROR: File does not exist!")
            self.patch_button.config(state="disabled")
            return
        
        # Display file info
        self.status_text.insert(tk.END, f"File: {os.path.basename(file_path)}\n")
        self.status_text.insert(tk.END, f"Path: {os.path.dirname(file_path)}\n")
        self.status_text.insert(tk.END, f"Size: {file_info['size']:,} bytes ({file_info['size_mb']:.2f} MB)\n")
        self.status_text.insert(tk.END, f"MD5: {file_info['md5']}\n\n")
        
        # Check if patching is needed
        needs_patch, status_msg, patch_info = self.patcher.identify_esm_version(file_path)
        
        self.status_text.insert(tk.END, f"Status: {status_msg}\n")
        
        if needs_patch:
            self.patch_info = patch_info
            self.status_text.insert(tk.END, f"\n✓ This file can be patched for VR compatibility\n")
            self.status_text.insert(tk.END, f"Patch to apply: {patch_info['description']}\n")
            self.patch_button.config(state="normal")
        else:
            self.patch_info = None
            self.patch_button.config(state="disabled")
            if "Already patched" in status_msg:
                self.status_text.insert(tk.END, "\n✓ This file is already VR-compatible!\n")
            elif "Unknown" in status_msg:
                self.status_text.insert(tk.END, "\n⚠ Unknown file version - cannot patch\n")
        
        # Check for backup
        backup_path = file_path + ".backup"
        if os.path.exists(backup_path):
            self.status_text.insert(tk.END, f"\n📁 Backup found: {os.path.basename(backup_path)}")
            self.restore_button.config(state="normal")
        else:
            self.restore_button.config(state="disabled")
    
    def update_progress(self, value: int, text: str):
        """Update progress bar and label"""
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.root.update()
    
    def apply_patch(self):
        """Apply the patch to the selected file"""
        if not self.selected_file or not self.patch_info:
            return
        
        result = messagebox.askyesno(
            "Confirm Patch",
            f"This will patch:\n{self.selected_file}\n\nA backup will be created.\n\nContinue?"
        )
        
        if not result:
            return
        
        # Disable buttons during patching
        self.patch_button.config(state="disabled")
        self.restore_button.config(state="disabled")
        
        try:
            # Create backup
            self.update_progress(10, "Creating backup...")
            success, backup_msg = self.patcher.create_backup(self.selected_file)
            
            if not success:
                messagebox.showerror("Backup Failed", f"Failed to create backup:\n{backup_msg}")
                return
            
            # Apply patch
            success, patch_msg = self.patcher.apply_patch(
                self.selected_file,
                self.patch_info,
                self.update_progress
            )
            
            self.update_progress(100, "Complete!")
            
            if success:
                messagebox.showinfo("Success", patch_msg)
                # Re-analyze the file to show new status
                self.analyze_file(self.selected_file)
            else:
                messagebox.showerror("Patch Failed", f"Failed to apply patch:\n{patch_msg}")
                
                # Offer to restore backup
                if self.patcher.backup_created:
                    restore = messagebox.askyesno(
                        "Restore Backup?",
                        "Would you like to restore the original file from backup?"
                    )
                    if restore:
                        self.restore_backup()
        
        finally:
            # Reset progress
            self.update_progress(0, "")
            
            # Re-enable buttons as appropriate
            if self.patch_info:
                self.patch_button.config(state="normal")
            if os.path.exists(self.selected_file + ".backup"):
                self.restore_button.config(state="normal")
    
    def restore_backup(self):
        """Restore from backup"""
        if not self.selected_file:
            return
        
        result = messagebox.askyesno(
            "Confirm Restore",
            f"This will restore the original file from backup.\n\nContinue?"
        )
        
        if not result:
            return
        
        success, msg = self.patcher.restore_backup(self.selected_file)
        
        if success:
            messagebox.showinfo("Success", msg)
            # Re-analyze the file
            self.analyze_file(self.selected_file)
        else:
            messagebox.showerror("Restore Failed", f"Failed to restore backup:\n{msg}")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
Fallout 4 ESM Patcher - Help

PURPOSE:
This tool patches Next-Gen Fallout4.esm files to make them compatible 
with Fallout 4 VR, Fallout: London, and other mods that require the 
older ESM format.

HOW TO USE:
1. Click "Auto-Detect" to find Fallout 4 installations
   OR click "Browse Folder" to select your Fallout 4 folder

2. The tool will automatically find Fallout4.esm in the selected folder
   (checks both the root folder and Data subfolder)

3. The tool will analyze the file and determine if patching is needed

4. If the file needs patching, click "Apply Patch"
   - A backup will be created automatically
   - The original file will be patched

5. If something goes wrong, use "Restore Backup" to revert

SUPPORTED VERSIONS:
- Next-Gen ESM files that need patching:
  • 330,777,465 bytes (323,025 KB variant)
  • 330,553,163 bytes (322,806 KB variant)

- Already compatible versions (no patching needed):
  • 330,745,373 bytes (315.42 MB) - Compatible version
  • ~58-59 MB files - Already patched versions

NOTES:
- Always creates a backup before patching
- Check the log file for detailed information
- Make sure Fallout 4 is not running when patching
- Works for both VR and non-VR mod compatibility

For more information, visit the Nexus Mods page.
        """
        
        messagebox.showinfo("Help", help_text)
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()


def main():
    """Main entry point"""
    try:
        # Check if running with command line arguments
        if len(sys.argv) > 1:
            # Command line mode
            if sys.argv[1] == "--help" or sys.argv[1] == "-h":
                print(__doc__)
                print("\nUsage:")
                print("  GUI Mode: Run without arguments")
                print("  CLI Mode: esm_patcher.py <path_to_fallout4.esm_or_folder>")
                print("  Help: esm_patcher.py --help")
                print("\nExamples:")
                print('  esm_patcher.py "C:\\Games\\Fallout 4"')
                print('  esm_patcher.py "C:\\Games\\Fallout 4\\Data\\Fallout4.esm"')
                sys.exit(0)
            
            # CLI patching mode
            input_path = sys.argv[1]
            esm_path = None
            
            # Check if it's a file or directory
            if os.path.isfile(input_path) and input_path.lower().endswith('.esm'):
                esm_path = input_path
            elif os.path.isdir(input_path):
                # Search for Fallout4.esm in the directory
                search_locations = [
                    os.path.join(input_path, "Fallout4.esm"),
                    os.path.join(input_path, "Data", "Fallout4.esm"),
                    os.path.join(input_path, "data", "Fallout4.esm"),
                ]
                
                for location in search_locations:
                    if os.path.exists(location):
                        esm_path = location
                        print(f"Found Fallout4.esm at: {esm_path}")
                        break
                
                if not esm_path:
                    print(f"Error: Fallout4.esm not found in {input_path}")
                    print("Please specify the game folder or the direct path to Fallout4.esm")
                    sys.exit(1)
            else:
                print(f"Error: Invalid path: {input_path}")
                print("Please specify a folder or .esm file")
                sys.exit(1)
            
            patcher = ESMPatcher()
            
            # Verify dependencies
            deps_ok, deps_msg = patcher.verify_dependencies()
            if not deps_ok:
                print(f"Error: {deps_msg}")
                sys.exit(1)
            
            # Analyze file
            needs_patch, status_msg, patch_info = patcher.identify_esm_version(esm_path)
            print(f"Status: {status_msg}")
            
            if not needs_patch:
                if "compatible" in status_msg.lower():
                    print("File is already compatible with mods!")
                else:
                    print("File cannot be patched.")
                sys.exit(0)
            
            # Create backup
            print("Creating backup...")
            success, backup_msg = patcher.create_backup(esm_path)
            if not success:
                print(f"Backup failed: {backup_msg}")
                sys.exit(1)
            print(f"Backup created: {backup_msg}")
            
            # Apply patch
            print("Applying patch...")
            success, patch_msg = patcher.apply_patch(esm_path, patch_info)
            
            if success:
                print(f"Success! {patch_msg}")
            else:
                print(f"Patch failed: {patch_msg}")
                sys.exit(1)
        
        else:
            # GUI mode
            app = PatcherGUI()
            app.run()
    
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()