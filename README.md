# Wireless Device Battery Monitor

A lightweight Windows system tray application that displays the battery level of your wireless devices (mice, keyboards, gamepads, headsets).

## Features

✨ **Multi-device support** - Monitor multiple devices simultaneously  
🖱️ **Device-specific icons** - Mouse, keyboard, gamepad, and headset icons  
📊 **Large, readable battery numbers** - Easy to see at a glance  
🔋 **Real-time monitoring** - Automatic battery updates  
⚡ **Charging status indicator** - Shows when devices are charging  
🎨 **Color-coded levels** - Green (good), Orange (medium), Red (low)  
🚀 **Easy setup** - GUI configuration with progress tracking  
💾 **Persistent settings** - Remembers your device selection  
🏃 **Auto-start support** - Optionally launch on Windows startup  
🪶 **Lightweight** - Minimal system resource usage

## Supported Devices

### Fully Supported
- **SteelSeries** wireless mice (via rivalcfg library)
  - Aerox 3 Wireless, Rival 3 Wireless, Rival 650 Wireless, and more
  - [→ Full list of SteelSeries devices](https://flozz.github.io/rivalcfg/devices/index.html)

### Experimental Support
- **Logitech** wireless devices (HID++ protocol)
- **Razer** wireless devices (OpenRazer or direct HID)
- **Microsoft** Xbox wireless controllers
- **Corsair** wireless devices (limited)
- Other HID battery-capable devices

## Installation

### Prerequisites

- **Windows 10/11**
- **Python 3.8 or higher** ([Download Python](https://www.python.org/downloads/))

### Quick Install

1. **Clone or download the repository**
   ```bash
   git clone https://github.com/pasrtelaria/mouse_battery.git
   cd mouse_battery
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the launcher** (Easiest way!)
   ```bash
   python start.py
   ```
   Or just double-click `start.py`

## First Time Setup

When you run `start.py` for the first time:

1. **Automatic GUI Launch**: Device selection window opens automatically
2. **Progress Dialog**: Shows scanning progress with ETA (~60 seconds)
3. **Select Devices**: Check the wireless devices you want to monitor
4. **Save**: Click "💾 Save & Apply"
5. **Auto-Start**: Tray icons appear automatically - Done! ✨

### Visual Guide

**Step 1: Loading Dialog**
```
┌─────────────────────────────────────────┐
│  🔍 Scanning for Wireless Devices...   │
│  [████████████░░░░░░░░░░░] 65%        │
│  Checking wireless indicators...        │
│  Estimated time remaining: ~22 seconds  │
└─────────────────────────────────────────┘
```

**Step 2: Device Selection**
- See all detected wireless devices
- Battery levels and charging status
- Check boxes for devices to monitor
- Device type icons (🖱️ 🎮 ⌨️ 🎧)

**Step 3: Tray Icons**
- One icon per selected device
- Shows device type + battery %
- Color-coded by battery level
- Right-click for refresh/settings

## Usage

### Running the Monitor

**Recommended:**
```bash
python start.py
```

**Alternative:**
```bash
python mouse_battery_tray.py
```

### Changing Monitored Devices

Run the settings GUI:
```bash
python device_settings_gui.py
```

Then restart the tray monitor.

## Usage

### Running the App

Simply double-click `mouse_battery_tray.py` or run:
```bash
python mouse_battery_tray.py
```

The app will appear in your system tray showing your mouse battery percentage.

### Auto-start on Windows Boot

To make the app start automatically when Windows boots:

```bash
python setup_startup.py
```

This will create a shortcut in your Windows Startup folder.

**To remove from startup:**
1. Press `Win + R`
2. Type `shell:startup` and press Enter
3. Delete the "Mouse Battery Monitor" shortcut

### System Tray Icon

Right-click the tray icon for options:
- **Refresh** - Manually update battery level
- **Exit** - Close the application

## How It Works

The application:
1. Uses the `rivalcfg` library to communicate with your SteelSeries mouse via HID protocol
2. Reads battery level and charging status
3. Updates a system tray icon with the current battery percentage
4. Refreshes automatically every few minutes

### Battery shows wrong percentage

**Solution:**
- Wait a few seconds for the first update
- Try the "Refresh" option in the system tray menu
- Restart the application

### App doesn't start

**Solution:**
1. Verify Python is installed: `python --version`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check if your mouse is supported by rivalcfg

### Building from Source

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python mouse_battery_tray.py`

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Requirements

See `requirements.txt` for the full list. Key dependencies:
- `rivalcfg` - SteelSeries device communication
- `pystray` - System tray integration
- `Pillow` - Icon generation
- `hidapi` - HID device access

## Credits

- [rivalcfg](https://github.com/flozz/rivalcfg) by [@flozz](https://github.com/flozz) - SteelSeries device library
- Inspired by similar battery monitoring tools for other mouse brands

## Acknowledgments

Special thanks to:
- The rivalcfg community for reverse-engineering SteelSeries protocols

**Star this repo if you find it useful!**
