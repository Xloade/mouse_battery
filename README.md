# Mouse Battery Monitor 🖱️🔋

A lightweight Windows system tray application that displays the battery level of your SteelSeries wireless mouse.

## Features

**Real-time battery monitoring** - See your mouse battery level at a glance  
**System tray integration** - Runs quietly in your system tray  
**Charging status** - Shows when your mouse is charging  
**Auto-start support** - Optionally launch on Windows startup  
**Lightweight** - Minimal system resource usage  
**No bloatware** - Get battery info without installing SteelSeries GG

## Supported Devices

This application uses the [rivalcfg](https://github.com/flozz/rivalcfg) library, which supports:

- SteelSeries Aerox 3 Wireless
- SteelSeries Rival 3 Wireless
- SteelSeries Rival 650 Wireless
- SteelSeries Sensei Ten Wireless
- And many more SteelSeries wireless mice

[→ See full list of supported devices](https://flozz.github.io/rivalcfg/devices/index.html)

## Installation

### Prerequisites

- **Windows 10/11**
- **Python 3.8 or higher** ([Download Python](https://www.python.org/downloads/))

### Quick Install

1. **Clone the repository**
   ```bash
   git clone https://github.com/pasrtelaria/mouse_battery.git
   cd mouse_battery
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python mouse_battery_tray.py
   ```

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
