import sys
import time
import threading
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item
from app import UniversalBatteryMonitor, BatteryDevice

class MouseBatteryTray:
    def __init__(self):
        self.monitor = UniversalBatteryMonitor()
        self.icon = None
        self.running = True
        self.current_battery = None
        self.update_interval = 60  # Update every 60 seconds
        
    def create_icon_image(self, battery_level):
        """Create an icon with the battery percentage text"""
        # Create a 64x64 image
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='black')
        draw = ImageDraw.Draw(image)
        
        # Determine color based on battery level
        if battery_level >= 35:
            color = (0, 255, 0)  # Green
        else:
            color = (255, 0, 0)  # Red
        
        # Draw battery text
        text = str(battery_level)
        
        # Try to use a font, fallback to default if not available
        try:
            # Use a larger font for better visibility
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw the text
        draw.text((x, y), text, fill=color, font=font)
        
        return image
    
    def get_mouse_battery(self):
        """Scan for mouse batteries and return the first one found"""
        try:
            devices = self.monitor.scan_all()
            
            # Filter for mouse devices (look for mouse in the name)
            mouse_devices = [d for d in devices if 'mouse' in d.name.lower()]
            
            if mouse_devices:
                return mouse_devices[0]
            elif devices:
                # If no specific mouse found, return first device
                return devices[0]
            else:
                return None
        except Exception as e:
            print(f"Error scanning battery: {e}")
            return None
    
    def update_battery(self):
        """Background thread to update battery level"""
        while self.running:
            device = self.get_mouse_battery()
            
            if device:
                self.current_battery = device.battery_level
                
                # Update icon with new battery level
                if self.icon:
                    self.icon.icon = self.create_icon_image(device.battery_level)
                    self.icon.title = f"Mouse Battery: {device.battery_level}%"
            else:
                # No device found
                if self.icon:
                    self.icon.icon = self.create_icon_image(0)
                    self.icon.title = "Mouse Battery: No device found"
            
            # Wait before next update
            time.sleep(self.update_interval)
    
    def on_quit(self, icon, item):
        """Handle quit action"""
        self.running = False
        icon.stop()
    
    def on_refresh(self, icon, item):
        """Handle manual refresh"""
        device = self.get_mouse_battery()
        if device:
            self.current_battery = device.battery_level
            icon.icon = self.create_icon_image(device.battery_level)
            icon.title = f"Mouse Battery: {device.battery_level}%"
    
    def setup_menu(self):
        """Create the context menu for the tray icon"""
        return pystray.Menu(
            item('Refresh Now', self.on_refresh),
            item('Quit', self.on_quit)
        )
    
    def run(self):
        """Start the system tray application"""
        # Initial scan
        device = self.get_mouse_battery()
        
        if device:
            initial_battery = device.battery_level
            title = f"Mouse Battery: {initial_battery}%"
        else:
            initial_battery = 0
            title = "Mouse Battery: Scanning..."
        
        # Create the tray icon
        icon_image = self.create_icon_image(initial_battery)
        self.icon = pystray.Icon(
            "mouse_battery",
            icon_image,
            title,
            menu=self.setup_menu()
        )
        
        # Start the background update thread
        update_thread = threading.Thread(target=self.update_battery, daemon=True)
        update_thread.start()
        
        # Run the icon (this blocks until quit)
        self.icon.run()


def main():
    print("Starting Mouse Battery Monitor...")
    print("The application will appear in your system tray.")
    
    app = MouseBatteryTray()
    app.run()


if __name__ == "__main__":
    main()
