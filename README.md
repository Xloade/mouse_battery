# Wireless Device Battery Monitor

A lightweight Windows system tray application that monitors and displays battery levels for multiple wireless devices simultaneously - mice, keyboards, gamepads, headsets, and more.

## Features

✨ **Multi-device support** - Monitor multiple devices simultaneously  
🖱️ **Device-specific icons** - Mouse, keyboard, gamepad, and headset icons  
📊 **Large, readable battery numbers** - Easy to see at a glance  
🔋 **Real-time monitoring** - Automatic battery updates every few minutes  
⚡ **Charging status indicator** - Shows when devices are charging  
🎨 **Color-coded levels** - Green (good), Orange (medium), Red (low)  
🚀 **Easy setup** - GUI configuration with progress tracking  
💾 **Persistent settings** - Remembers your device selection  
💾 **Battery caching** - Displays last known level instantly on startup  
🏃 **Auto-start support** - Optionally launch on Windows startup  
🪶 **Lightweight** - Minimal system resource usage

## Supported Devices

This application uses Windows HID (Human Interface Device) protocol and device APIs to detect wireless devices with battery reporting capabilities. Compatible with most modern wireless peripherals including:

- **Logitech** wireless devices (mice, keyboards, headsets)
- **SteelSeries** wireless devices (via rivalcfg library)
- **Razer** wireless devices
- **Microsoft** wireless devices and Xbox controllers
- **Corsair** wireless devices
- Most HID-compliant wireless peripherals with battery reporting

## Installation

### Prerequisites

- **Windows 10/11**
- **Python 3.8 or higher** ([Download Python](https://www.python.org/downloads/))
  - During Python installation, check "Add Python to PATH"

### Quick Install

1. **Clone or download the repository**
   ```bash
   git clone https://github.com/yourusername/mouse_battery.git
   cd mouse_battery
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the launcher** (Easiest way!)
   - **Windows**: Double-click `start.bat`
   - **Command line**: `python device_settings_gui.py`

## First Time Setup

When you run `start.bat` or `device_settings_gui.py` for the first time:

1. **Progress Dialog**: Shows scanning progress with ETA (~30-60 seconds)
   - The application scans all HID devices connected to your system
   - Identifies wireless devices with battery reporting

2. **Device Selection Window**: 
   - Check the wireless devices you want to monitor
   - View current battery levels and charging status
   - See device type icons (🖱️ Mouse, ⌨️ Keyboard, 🎮 Gamepad, 🎧 Headset)

3. **Save Configuration**: 
   - Click "💾 Save & Apply"
   - Settings are saved to `device_config.json`
   - Battery levels are cached to `battery_cache.json`

4. **Tray Monitor Launch**: 
   - The system tray monitor starts automatically
   - One icon appears per selected device
   - Icons update automatically every few minutes

### Visual Guide

**Step 1: Scanning Progress**
```
┌─────────────────────────────────────────┐
│  🔍 Scanning for Wireless Devices...   │
│  [████████████░░░░░░░░░░░] 65%        │
│  Checking device capabilities...        │
│  Estimated time remaining: ~22 seconds  │
└─────────────────────────────────────────┘
```

**Step 2: Device Selection**
- All detected wireless devices listed
- Battery levels displayed in real-time
- Check boxes for devices to monitor
- Device type automatically detected

**Step 3: System Tray**
- Individual icon for each device
- Shows device icon + battery percentage
- Color-coded: Green (>50%), Orange (20-50%), Red (<20%)
- Right-click for options: Refresh, Settings, Exit

## Usage

### Running the Monitor

**First time or to change settings:**
- Double-click `start.bat`, or
- Run `python device_settings_gui.py`

**After configuration is saved:**
- The tray monitor runs in the background
- Close the settings window after saving
- Icons persist in system tray

### Changing Monitored Devices

To add/remove devices or update settings:

1. Run `start.bat` or `python device_settings_gui.py`
2. Modify your device selections
3. Click "💾 Save & Apply"
4. The tray monitor will restart automatically with updated settings

### Auto-start on Windows Boot

The settings GUI includes an **"Add to Windows Startup"** checkbox:

1. Open `device_settings_gui.py`
2. Check **"Add to Windows Startup"** at the bottom
3. Click "💾 Save & Apply"

This creates a registry entry to launch the monitor on Windows login.

**To disable auto-start:**
- Uncheck the box in the settings GUI, or
- Press `Win + R`, type `shell:startup`, and delete any shortcuts

### System Tray Icons

Each monitored device has its own tray icon showing:
- Device type icon (mouse, keyboard, gamepad, or headset)
- Battery percentage (large, readable numbers)
- Color-coded background (green/orange/red)

**Right-click any icon for:**
- **Refresh** - Manually update battery level
- **Settings** - Open configuration GUI
- **Exit** - Close the application

## How It Works

The application uses multiple detection methods:

1. **HID Protocol**: Directly queries HID devices for battery reports
2. **Windows APIs**: Uses Windows device enumeration to find wireless devices
3. **Device Classification**: Analyzes HID usage tables to identify device types
4. **Battery Caching**: Stores last known battery levels for instant display on startup
5. **SteelSeries Support**: Uses `rivalcfg` library for enhanced SteelSeries device support

The monitor:
- Updates battery levels every few minutes
- Displays cached values immediately on startup
- Shows charging status when devices are plugged in
- Persists configuration across restarts

## Troubleshooting

### Battery shows wrong percentage

**Solution:**
- Wait a few seconds for the first update
- Try the "Refresh" option from the tray icon
- Battery caching displays last known value until next update

### No devices detected

**Solution:**
1. Ensure devices are powered on and connected
2. Try unplugging/reconnecting wireless dongles
3. Run the settings GUI as Administrator
4. Check Device Manager for HID-compliant devices

### App doesn't start

**Solution:**
1. Verify Python is installed: `python --version`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check for error messages in the console

## Project Structure

```
mouse_battery/
├── start.bat                  # Windows launcher script
├── device_settings_gui.py     # Configuration GUI with device selection
├── mouse_battery_tray.py      # System tray monitor application
├── app.py                     # Battery detection and device scanning
├── parser.py                  # Device classification and HID parsing
├── device_config.json         # Saved device configuration
├── battery_cache.json         # Cached battery levels
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Requirements

Key dependencies (see `requirements.txt` for complete list):
- `pystray>=0.19.5` - System tray integration
- `Pillow>=10.0.0` - Icon generation
- `hidapi>=0.14.0` - HID device access
- `rivalcfg>=4.0.0` - SteelSeries device communication
- `pywin32>=306` - Windows API access
- `winshell>=0.6` - Windows shell integration

## Contributing

Contributions are welcome! Areas for improvement:
- Support for additional device brands
- Enhanced battery reporting accuracy
- Custom icon themes
- Notification alerts for low battery

Please feel free to submit Pull Requests or open Issues.

## License

This project is open source. Feel free to use and modify as needed.

## Credits

- [rivalcfg](https://github.com/flozz/rivalcfg) by [@flozz](https://github.com/flozz) - SteelSeries device library
- HID API and protocol documentation from various sources
- Inspired by similar battery monitoring tools

---

**⭐ Star this repo if you find it useful!**
