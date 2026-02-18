import sys
import time
import json
import threading
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item
from app import UniversalBatteryMonitor, BatteryDevice


# Battery cache file
BATTERY_CACHE_FILE = Path("battery_cache.json")


def save_battery_cache(device_batteries: Dict[str, Dict]):
    """Save battery levels to cache file
    
    Args:
        device_batteries: Dict mapping device_id to {'battery': int, 'charging': bool, 'timestamp': float}
    """
    try:
        cache_data = {
            'timestamp': time.time(),
            'devices': device_batteries
        }
        with open(BATTERY_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save battery cache: {e}")


def load_battery_cache() -> Dict[str, Dict]:
    """Load battery levels from cache file
    
    Returns:
        Dict mapping device_id to {'battery': int, 'charging': bool, 'timestamp': float}
    """
    try:
        if not BATTERY_CACHE_FILE.exists():
            return {}
        
        with open(BATTERY_CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        devices = cache_data.get('devices', {})
        cache_age = time.time() - cache_data.get('timestamp', 0)
        print(f"Loaded battery cache (age: {cache_age:.0f}s)")
        
        return devices
    except Exception as e:
        print(f"Warning: Could not load battery cache: {e}")
        return {}


class DeviceIcon:
    """Represents a single device with its tray icon"""
    def __init__(self, device_config: Dict, monitor: UniversalBatteryMonitor):
        self.config = device_config
        self.monitor = monitor
        self.icon = None
        self.current_battery = None
        self.device_type = device_config.get('type', ' Device')
        self.device_name = device_config.get('name', 'Unknown Device')
        self.vid = device_config.get('vid', 0)
        self.pid = device_config.get('pid', 0)
    
    def create_icon_image(self, battery_level: int) -> Image.Image:
        """Create an icon with device type symbol and battery percentage"""
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Determine color based on battery level
        if battery_level >= 50:
            color = (0, 200, 0)  # Green
        elif battery_level >= 25:
            color = (255, 165, 0)  # Orange
        else:
            color = (255, 0, 0)  # Red
        
        # Draw device type icon/symbol at top
        device_symbol = self.get_device_symbol()
        try:
            symbol_font = ImageFont.truetype("seguiemj.ttf", 35)  # Reduced from 30
        except:
            try:
                symbol_font = ImageFont.truetype("arial.ttf", 18)
            except:
                symbol_font = ImageFont.load_default()
        
        # Draw symbol at top center with more padding
        bbox = draw.textbbox((0, 0), device_symbol, font=symbol_font)
        symbol_width = bbox[2] - bbox[0]
        symbol_height = bbox[3] - bbox[1]
        symbol_x = (width - symbol_width) // 2
        symbol_y = 4  # More padding from top
        draw.text((symbol_x, symbol_y), device_symbol, fill=color, font=symbol_font)
        
        # Draw battery percentage at bottom (BIGGER for visibility)
        battery_text = str(battery_level)
        try:
            battery_font = ImageFont.truetype("arial.ttf", 50)  # Reduced from 50 to fit better
        except:
            battery_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), battery_text, font=battery_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (width - text_width) // 2
        text_y = height - text_height - 8  # More padding from bottom
        
        draw.text((text_x, text_y), battery_text, fill=color, font=battery_font)
        
        return image
    
    def get_device_symbol(self) -> str:
        """Get symbol based on device type"""
        if '🖱️' in self.device_type or 'Mouse' in self.device_type:
            return '🖱'
        elif '⌨️' in self.device_type or 'Keyboard' in self.device_type:
            return '⌨'
        elif '🎮' in self.device_type or 'Gamepad' in self.device_type:
            return '🎮'
        elif '🎧' in self.device_type or 'Headset' in self.device_type:
            return '🎧'
        else:
            return '📱'
    
    def find_device(self) -> Optional[BatteryDevice]:
        """Find this device using targeted scan (much faster than full scan)"""
        try:
            # Use targeted scan for this specific VID/PID
            device = self.monitor.scan_specific_device(self.vid, self.pid)
            if device:
                return device
            
            # Fallback: full scan if targeted scan failed
            print(f"Targeted scan failed for {self.device_name}, falling back to full scan...")
            devices = self.monitor.scan_all()
            
            for device in devices:
                device_vid = device.details.get('vid', 0)
                device_pid = device.details.get('pid', 0)
                
                if device_vid == self.vid and device_pid == self.pid:
                    return device
            
            # Try matching by name if VID/PID didn't match
            for device in devices:
                if device.name == self.device_name:
                    return device
                    
        except Exception as e:
            print(f"Error finding device {self.device_name}: {e}")
        
        return None


class MouseBatteryTray:
    def __init__(self):
        self.monitor = UniversalBatteryMonitor()
        self.device_icons: List[DeviceIcon] = []
        self.running = True
        self.update_interval = 60  # Update every 60 seconds
        self.config_file = Path("device_config.json")
        self.battery_cache = load_battery_cache()  # Load cached battery levels
        
    def load_config(self) -> bool:
        """Load device configuration"""
        try:
            if not self.config_file.exists():
                print("No config file found. Please run device_settings_gui.py first.")
                return False
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            selected_devices = config.get('selected_devices', [])
            self.update_interval = config.get('update_interval', 60)
            
            if not selected_devices:
                print("No devices selected. Please run device_settings_gui.py to select devices.")
                return False
            
            # Create DeviceIcon for each selected device
            for device_config in selected_devices:
                device_icon = DeviceIcon(device_config, self.monitor)
                self.device_icons.append(device_icon)
            
            print(f"Loaded {len(self.device_icons)} device(s) from config")
            return True
            
        except Exception as e:
            print(f"Error loading config: {e}")
            return False
    
    def update_device_battery(self, device_icon: DeviceIcon):
        """Update a single device's battery and icon"""
        try:
            device = device_icon.find_device()
            
            if device:
                device_icon.current_battery = device.battery_level
                
                # Update cache
                device_id = f"{device_icon.vid:04x}:{device_icon.pid:04x}"
                self.battery_cache[device_id] = {
                    'battery': device.battery_level,
                    'charging': device.charging,
                    'timestamp': time.time()
                }
                save_battery_cache(self.battery_cache)
                
                if device_icon.icon:
                    device_icon.icon.icon = device_icon.create_icon_image(device.battery_level)
                    charging_str = " (Charging)" if device.charging else ""
                    device_icon.icon.title = f"{device_icon.device_name}: {device.battery_level}%{charging_str}"
            else:
                # Device not found
                if device_icon.icon:
                    device_icon.icon.icon = device_icon.create_icon_image(0)
                    device_icon.icon.title = f"{device_icon.device_name}: Not found"
        except Exception as e:
            print(f"Error updating {device_icon.device_name}: {e}")
    
    def update_all_batteries(self):
        """Background thread to update all device battery levels"""
        while self.running:
            for device_icon in self.device_icons:
                self.update_device_battery(device_icon)
            
            # Wait before next update
            time.sleep(self.update_interval)
    
    def on_quit_all(self):
        """Handle quit action - stops all icons"""
        self.running = False
        for device_icon in self.device_icons:
            if device_icon.icon:
                device_icon.icon.stop()
    
    def on_refresh_all(self):
        """Handle manual refresh of all devices"""
        for device_icon in self.device_icons:
            self.update_device_battery(device_icon)
    
    def on_open_settings(self):
        """Open device settings GUI"""
        import subprocess
        import sys
        
        # Launch device settings GUI
        subprocess.Popen([sys.executable, "device_settings_gui.py"])
    
    def setup_menu(self, device_icon: DeviceIcon):
        """Create the context menu for a device's tray icon"""
        def refresh_this(icon, item):
            self.update_device_battery(device_icon)
        
        def refresh_all(icon, item):
            self.on_refresh_all()
        
        def open_settings(icon, item):
            self.on_open_settings()
        
        def quit_all(icon, item):
            self.on_quit_all()
        
        return pystray.Menu(
            item(f'Refresh {device_icon.device_name}', refresh_this),
            item('Refresh All Devices', refresh_all),
            pystray.Menu.SEPARATOR,
            item('Device Settings...', open_settings),
            pystray.Menu.SEPARATOR,
            item('Quit All', quit_all)
        )
    
    def start_device_icon(self, device_icon: DeviceIcon):
        """Start a single device's tray icon"""
        # Try to get battery from cache first for instant display
        device_id = f"{device_icon.vid:04x}:{device_icon.pid:04x}"
        cached_data = self.battery_cache.get(device_id)
        
        if cached_data:
            initial_battery = cached_data.get('battery', 0)
            is_charging = cached_data.get('charging', False)
            charging_str = " (Cached)" if not is_charging else " (Cached, Charging)"
            title = f"{device_icon.device_name}: {initial_battery}%{charging_str}"
            print(f"Using cached battery for {device_icon.device_name}: {initial_battery}%")
        else:
            initial_battery = 0
            title = f"{device_icon.device_name}: Loading..."
        
        # Create the tray icon
        icon_image = device_icon.create_icon_image(initial_battery)
        device_icon.icon = pystray.Icon(
            f"battery_{device_icon.vid:04x}_{device_icon.pid:04x}",
            icon_image,
            title,
            menu=self.setup_menu(device_icon)
        )
        
        # Run the icon (this blocks until quit)
        device_icon.icon.run()
    
    def run(self):
        #Start the system tray application
        if not self.load_config():
            print("\nTo configure devices:")
            print("  python device_settings_gui.py")
            return
        
        print(f"Starting battery monitor for {len(self.device_icons)} device(s)...")
        
        # Start the background update thread
        update_thread = threading.Thread(target=self.update_all_batteries, daemon=True)
        update_thread.start()
        
        # Start tray icons for each device in separate threads
        icon_threads = []
        for i, device_icon in enumerate(self.device_icons):
            if i == 0:
                # Run first icon in main thread (required for proper tray behavior)
                self.start_device_icon(device_icon)
            else:
                # Run additional icons in separate threads
                thread = threading.Thread(
                    target=self.start_device_icon,
                    args=(device_icon,),
                    daemon=False
                )
                thread.start()
                icon_threads.append(thread)
                time.sleep(0.2)  # Small delay between starting icons
        
        # Wait for all icon threads to finish
        for thread in icon_threads:
            thread.join()


def main():
    print("Starting Mouse Battery Monitor...")
    print("The application will appear in your system tray.")
    
    app = MouseBatteryTray()
    app.run()


if __name__ == "__main__":
    main()
