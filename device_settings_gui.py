import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
import subprocess
import sys
import os
from pathlib import Path
from app import UniversalBatteryMonitor
from typing import Dict, List

try:
    import winreg
    WINDOWS_REGISTRY_AVAILABLE = True
except ImportError:
    WINDOWS_REGISTRY_AVAILABLE = False


class LoadingDialog:
    """Progress dialog with ETA for device scanning"""
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("")
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"400x150+{x}+{y}")
        
        # Main frame
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            frame,
            text="🔍 Scanning for Wireless Devices...",
            font=('Arial', 12, 'bold')
        )
        title_label.pack(pady=(0, 15))
        
        # Progress bar
        self.progress = ttk.Progressbar(
            frame,
            mode='determinate',
            length=350
        )
        self.progress.pack(pady=10)
        
        # Status label
        self.status_label = ttk.Label(
            frame,
            text="Initializing scan...",
            font=('Arial', 9)
        )
        self.status_label.pack(pady=5)
        
        # ETA label
        self.eta_label = ttk.Label(
            frame,
            text="Estimated time: ~60 seconds",
            font=('Arial', 9),
            foreground="gray"
        )
        self.eta_label.pack(pady=5)
        
        self.start_time = time.time()
        self.cancelled = False
    
    def update_progress(self, value: int, status: str):
        """Update progress bar and status"""
        self.progress['value'] = value
        self.status_label.config(text=status)
        
        # Calculate ETA
        elapsed = time.time() - self.start_time
        if value > 0:
            total_estimated = (elapsed / value) * 100
            remaining = total_estimated - elapsed
            if remaining > 0:
                self.eta_label.config(text=f"Estimated time remaining: ~{int(remaining)} seconds")
            else:
                self.eta_label.config(text="Almost done...")
        
        self.dialog.update()
    
    def close(self):
        """Close the dialog"""
        self.dialog.grab_release()
        self.dialog.destroy()


class DeviceSelectionGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mouse Battery Monitor - Device Settings")
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        
        self.monitor = UniversalBatteryMonitor()
        self.config_file = Path("device_config.json")
        self.cache_file = Path("device_cache.json")
        self.devices = []
        self.selected_devices = []
        
        self.setup_ui()
        self.load_config()
        
        # Try loading from cache first for instant display
        if self.load_device_cache():
            self.status_label.config(text="Loaded from cache. Click 'Refresh' to rescan.", foreground="blue")
        else:
            # No cache available, perform initial scan
            self.scan_devices()
    
    def setup_ui(self):
        """Create the GUI layout"""
        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            title_frame,
            text="Select Wireless Devices to Monitor",
            font=('Arial', 14, 'bold')
        )
        title_label.pack()
        
        # Instructions
        info_label = ttk.Label(
            title_frame,
            text="Check the devices you want to monitor in the system tray",
            font=('Arial', 9)
        )
        info_label.pack(pady=5)
        
        # Device list frame
        list_frame = ttk.LabelFrame(self.root, text="Available Devices", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbar for device list
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview for devices
        columns = ('type', 'name', 'battery', 'charging')
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='tree headings',
            selectmode='extended',
            yscrollcommand=scrollbar.set
        )
        
        # Configure columns
        self.tree.heading('#0', text='✓')
        self.tree.heading('type', text='Type')
        self.tree.heading('name', text='Device Name')
        self.tree.heading('battery', text='Battery')
        self.tree.heading('charging', text='Status')
        
        self.tree.column('#0', width=30, stretch=False)
        self.tree.column('type', width=80)
        self.tree.column('name', width=350)
        self.tree.column('battery', width=80)
        self.tree.column('charging', width=80)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Bind checkbox toggle
        self.tree.bind('<Button-1>', self.on_tree_click)
        
        # Status label
        self.status_label = ttk.Label(self.root, text="Scanning devices...", foreground="gray")
        self.status_label.pack(pady=5)
        
        # Startup option frame
        startup_frame = ttk.Frame(self.root)
        startup_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.startup_var = tk.BooleanVar(value=self.check_startup_enabled())
        self.startup_checkbox = ttk.Checkbutton(
            startup_frame,
            text=" Run battery monitor on Windows startup",
            variable=self.startup_var,
            command=self.toggle_startup
        )
        self.startup_checkbox.pack(side=tk.LEFT)
        
        # Buttons frame
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        
        self.refresh_btn = ttk.Button(
            button_frame,
            text=" Refresh Devices",
            command=self.scan_devices
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(
            button_frame,
            text=" Save & Apply",
            command=self.save_and_apply
        )
        self.save_btn.pack(side=tk.RIGHT, padx=5)
        
        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.root.quit
        )
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def determine_device_type(self, device) -> str:
        """Determine device type from capabilities"""
        caps = device.details.get('capabilities', {})
        
        if caps.get('mouse'):
            return ' Mouse'
        elif caps.get('keyboard'):
            return ' Keyboard'
        elif caps.get('gamepad'):
            return ' Gamepad'
        elif 'headset' in device.name.lower() or 'headphone' in device.name.lower():
            return ' Headset'
        else:
            return ' Device'
    
    def scan_devices(self):
        """Scan for available wireless devices with progress dialog"""
        self.refresh_btn.config(state='disabled')
        self.save_btn.config(state='disabled')
        
        # Create loading dialog
        loading = LoadingDialog(self.root)
        
        # Scanning state
        scan_state = {
            'devices': None, 
            'error': None, 
            'progress': 0,
            'status': 'Starting...',
            'complete': False
        }
        
        def scan_thread():
            """Background thread for scanning"""
            try:
                # Progress updates
                scan_state['progress'] = 10
                scan_state['status'] = "May take a minute"
                time.sleep(0.2)
                
                scan_state['progress'] = 25
                scan_state['status'] = "May take a minute"
                time.sleep(0.2)
                
                scan_state['progress'] = 40
                scan_state['status'] = "May take a minute"
                
                # Actual scan (this takes ~1 minute)
                devices = self.monitor.scan_all()
                scan_state['devices'] = devices
                
                scan_state['progress'] = 90
                scan_state['status'] = "Processing results..."
                time.sleep(0.2)
                
                scan_state['progress'] = 100
                scan_state['status'] = "Complete!"
                time.sleep(0.3)
                
            except Exception as e:
                scan_state['error'] = str(e)
            finally:
                scan_state['complete'] = True
        
        def check_progress():
            """Check scan progress (called periodically from main thread)"""
            if not scan_state['complete']:
                # Update progress dialog
                loading.update_progress(scan_state['progress'], scan_state['status'])
                
                # Check again in 100ms
                self.root.after(100, check_progress)
            else:
                # Scan complete - close dialog and process results
                loading.close()
                self.process_scan_results(scan_state)
        
        # Start scan in background thread
        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()
        
        # Start checking progress (non-blocking)
        self.root.after(100, check_progress)
    
    def process_scan_results(self, scan_state):
        """Process scan results after scanning completes"""
        # Re-enable buttons first
        self.refresh_btn.config(state='normal')
        self.save_btn.config(state='normal')
        
        # Check for scan errors
        if scan_state['error']:
            messagebox.showerror("Error", f"Failed to scan devices:\n{scan_state['error']}")
            self.status_label.config(text="Scan failed", foreground="red")
            return
        
        try:
            self.devices = scan_state['devices']
            
            if not self.devices:
                self.status_label.config(text="No wireless devices found", foreground="orange")
                return
            
            # Populate tree with scanned devices
            self.populate_device_tree()
            
            self.status_label.config(
                text=f"Found {len(self.devices)} device(s). Select devices to monitor.",
                foreground="green"
            )
            
            # Save devices to cache for future use
            self.save_device_cache()
            
        except Exception as e:
            # Log the actual error for debugging
            print(f"DEBUG: Exception in process_scan_results: {e}")
            import traceback
            traceback.print_exc()
            print("Error", f"Failed to process scan results:\n{e}")
    
    def on_tree_click(self, event):
        """Handle tree item clicks for checkbox toggle"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "tree":
            item_id = self.tree.identify_row(event.y)
            if item_id:
                self.toggle_selection(item_id)
    
    def toggle_selection(self, item_id):
        """Toggle device selection"""
        current_tags = self.tree.item(item_id, 'tags')
        
        if 'checked' in current_tags:
            # Uncheck
            self.tree.item(item_id, text='☐', tags=('unchecked',))
        else:
            # Check
            self.tree.item(item_id, text='☑', tags=('checked',))
    
    def get_selected_devices(self) -> List[Dict]:
        """Get list of selected devices"""
        selected = []
        
        for item_id in self.tree.get_children():
            tags = self.tree.item(item_id, 'tags')
            if 'checked' in tags:
                # Find device by matching name
                values = self.tree.item(item_id, 'values')
                device_name = values[1]  # Name column
                
                # Find matching device
                for device in self.devices:
                    if device.name == device_name:
                        device_id = f"{device.details.get('vid', 0):04x}:{device.details.get('pid', 0):04x}"
                        selected.append({
                            'id': device_id,
                            'name': device.name,
                            'type': values[0],  # Type column
                            'vid': device.details.get('vid', 0),
                            'pid': device.details.get('pid', 0),
                        })
                        break
        
        return selected
    
    def save_and_apply(self):
        """Save selected devices to config file and launch tray"""
        selected = self.get_selected_devices()
        
        if not selected:
            result = messagebox.askyesno(
                "No Selection",
                "No devices selected. This will disable battery monitoring.\n\nContinue?"
            )
            if not result:
                return
        
        try:
            # Save config
            config = {
                'selected_devices': selected,
                'update_interval': 60
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Launch tray app immediately
            tray_script = Path(__file__).parent / "mouse_battery_tray.py"
            if tray_script.exists():
                subprocess.Popen(
                    [sys.executable, str(tray_script)],
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
            
            messagebox.showinfo(
                "Success",
                f"Saved {len(selected)} device(s).\n\n"
                "Tray application is starting..."
            )
            
            self.root.quit()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config:\n{e}")
    
    def load_config(self):
        """Load previously saved config"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                selected_devices = config.get('selected_devices', [])
                self.selected_devices = [d['id'] for d in selected_devices]
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            self.selected_devices = []
    
    def save_device_cache(self):
        """Save scanned devices to cache for faster loading"""
        try:
            cache_data = {
                'timestamp': time.time(),
                'devices': [
                    {
                        'name': device.name,
                        'battery_level': device.battery_level,
                        'charging': device.charging,
                        'source': device.source,
                        'details': device.details
                    }
                    for device in self.devices
                ]
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            print(f"Saved {len(self.devices)} devices to cache")
            
            # Also save battery levels to battery_cache.json for tray instant display
            battery_cache = {}
            for device in self.devices:
                if device.battery_level is not None:
                    device_id = f"{device.details.get('vid', 0):04x}:{device.details.get('pid', 0):04x}"
                    battery_cache[device_id] = {
                        'battery': device.battery_level,
                        'charging': device.charging,
                        'timestamp': time.time()
                    }
            
            battery_cache_file = Path("battery_cache.json")
            battery_cache_data = {
                'timestamp': time.time(),
                'devices': battery_cache
            }
            
            with open(battery_cache_file, 'w') as f:
                json.dump(battery_cache_data, f, indent=2)
            
            print(f"Saved battery cache for {len(battery_cache)} device(s)")
            
        except Exception as e:
            print(f"Warning: Could not save device cache: {e}")
    
    def load_device_cache(self) -> bool:
        """Load devices from cache and populate the tree. Returns True if successful."""
        try:
            if not self.cache_file.exists():
                return False
            
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check cache age (optionally skip if too old)
            cache_age = time.time() - cache_data.get('timestamp', 0)
            print(f"Cache age: {cache_age:.0f} seconds")
            
            # Reconstruct BatteryDevice objects
            from app import BatteryDevice
            cached_devices = cache_data.get('devices', [])
            self.devices = [
                BatteryDevice(
                    name=d['name'],
                    battery_level=d.get('battery_level'),
                    charging=d.get('charging', False),
                    source=d.get('source', 'cache'),
                    details=d.get('details', {})
                )
                for d in cached_devices
            ]
            
            if not self.devices:
                return False
            
            # Populate tree with cached devices
            self.populate_device_tree()
            
            return True
            
        except Exception as e:
            print(f"Warning: Could not load device cache: {e}")
            return False
    
    def populate_device_tree(self):
        """Populate the tree view with current devices list"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add devices to tree
        for device in self.devices:
            device_type = self.determine_device_type(device)
            battery_str = f"{device.battery_level}%" if device.battery_level is not None else "N/A"
            charging_str = "Charging" if getattr(device, 'charging', False) else "Not Charging"
            
            # Check if device was previously selected
            device_id = f"{device.details.get('vid', 0):04x}:{device.details.get('pid', 0):04x}"
            is_selected = device_id in self.selected_devices
            
            # Insert item
            item_id = self.tree.insert(
                '',
                'end',
                text='☑' if is_selected else '☐',
                values=(device_type, device.name, battery_str, charging_str),
                tags=('checked' if is_selected else 'unchecked',)
            )
    
    def check_startup_enabled(self) -> bool:
        """Check if startup is currently enabled"""
        if not WINDOWS_REGISTRY_AVAILABLE or sys.platform != 'win32':
            return False
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                value, _ = winreg.QueryValueEx(key, "MouseBatteryTray")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception as e:
            print(f"Error checking startup status: {e}")
            return False
    
    def enable_startup(self):
        """Enable running on Windows startup"""
        if not WINDOWS_REGISTRY_AVAILABLE or sys.platform != 'win32':
            messagebox.showerror(
                "Not Supported",
                "Startup configuration is only supported on Windows."
            )
            return False
        
        try:
            # Get path to start.py or tray script
            script_dir = Path(__file__).parent
            start_script = script_dir / "start.py"
            
            if not start_script.exists():
                start_script = script_dir / "mouse_battery_tray.py"
            
            # Create command with pythonw to hide console
            python_exe = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(python_exe):
                python_exe = sys.executable
            
            command = f'"{python_exe}" "{start_script}"'
            
            # Add to registry
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "MouseBatteryTray", 0, winreg.REG_SZ, command)
            winreg.CloseKey(key)
            
            print("Enabled startup: " + command)
            return True
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to enable startup:\n{e}"
            )
            return False
    
    def disable_startup(self):
        """Disable running on Windows startup"""
        if not WINDOWS_REGISTRY_AVAILABLE or sys.platform != 'win32':
            return False
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            try:
                winreg.DeleteValue(key, "MouseBatteryTray")
                winreg.CloseKey(key)
                print("Disabled startup")
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return True
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to disable startup:\n{e}"
            )
            return False
    
    def toggle_startup(self):
        """Toggle startup on/off based on checkbox state"""
        if self.startup_var.get():
            if not self.enable_startup():
                # Failed to enable, revert checkbox
                self.startup_var.set(False)
        else:
            if not self.disable_startup():
                # Failed to disable, revert checkbox
                self.startup_var.set(True)
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


def main():
    print("Opening device settings...")
    app = DeviceSelectionGUI()
    app.run()


if __name__ == "__main__":
    main()
