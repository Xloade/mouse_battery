"""
Script to add Mouse Battery Tray to Windows startup
"""
import os
import sys
import winshell
from win32com.client import Dispatch

def create_startup_shortcut():
    """Create a shortcut in the Windows Startup folder"""
    
    # Get the startup folder path
    startup_folder = winshell.startup()
    
    # Path to the Python executable in venv
    python_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              '.venv', 'Scripts', 'pythonw.exe')
    
    # Path to the script
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               'mouse_battery_tray.py')
    
    # Shortcut path
    shortcut_path = os.path.join(startup_folder, 'Mouse Battery Monitor.lnk')
    
    # Create shortcut
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = python_exe
    shortcut.Arguments = f'"{script_path}"'
    shortcut.WorkingDirectory = os.path.dirname(script_path)
    shortcut.IconLocation = python_exe
    shortcut.Description = "Mouse Battery Monitor - System Tray App"
    shortcut.save()
    
    print(f"✓ Startup shortcut created successfully!")
    print(f"  Location: {shortcut_path}")
    print(f"\nThe Mouse Battery Monitor will now start automatically when you log in.")
    print(f"\nTo disable auto-start, delete the shortcut from:")
    print(f"  {startup_folder}")
    
    return True

def remove_startup_shortcut():
    """Remove the startup shortcut"""
    startup_folder = winshell.startup()
    shortcut_path = os.path.join(startup_folder, 'Mouse Battery Monitor.lnk')
    
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)
        print(f"✓ Startup shortcut removed successfully!")
        print(f"  The app will no longer start automatically.")
        return True
    else:
        print(f"✗ No startup shortcut found.")
        print(f"  Location checked: {shortcut_path}")
        return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'remove':
        remove_startup_shortcut()
    else:
        create_startup_shortcut()

if __name__ == "__main__":
    main()
