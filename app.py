import sys
from typing import List, Dict, Optional

# Check dependencies
MISSING_DEPS = []

try:
    import hid
except ImportError:
    MISSING_DEPS.append("hidapi")

try:
    import asyncio
    from bleak import BleakScanner, BleakClient
    HAS_BLEAK = True
except ImportError:
    HAS_BLEAK = False
    MISSING_DEPS.append("bleak")

# Windows-specific imports
if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes

# Battery detection methods
class BatteryDevice:
    """Represents a battery-capable device"""
    def __init__(self, name: str, battery_level: int, charging: bool, 
                 source: str, details: Dict = None):
        self.name = name
        self.battery_level = battery_level
        self.charging = charging
        self.source = source  # 'windows_api', 'hid', 'bluetooth_le'
        self.details = details or {}
    
    def __str__(self):
        charging_str = " (Charging)" if self.charging else ""
        return f"{self.name}: {self.battery_level}%{charging_str} [{self.source}]"


class UniversalBatteryMonitor:
    """Universal battery monitor using multiple detection methods"""
    
    def __init__(self):
        self.devices: List[BatteryDevice] = []
    
    def scan_all(self) -> List[BatteryDevice]:
        """Scan for batteries using all available methods"""
        self.devices = []
        
        print("Scanning for battery devices using all methods...")
        print("=" * 60)
        
        # Method 1: Windows Battery API
        if sys.platform == 'win32':
            print("\n[1/3] Checking Windows Battery API...")
            try:
                windows_batteries = self._scan_windows_battery_api()
                self.devices.extend(windows_batteries)
                print(f"  Found {len(windows_batteries)} device(s)")
            except Exception as e:
                print(f"  Error: {e}")
        
        # Method 2: HID devices with vendor libraries
        print("\n[2/3] Checking HID devices...")
        try:
            hid_batteries = self._scan_hid_batteries()
            self.devices.extend(hid_batteries)
            print(f"  Found {len(hid_batteries)} device(s)")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Method 3: Bluetooth LE GATT
        if HAS_BLEAK:
            print("\n[3/3] Checking Bluetooth LE devices...")
            try:
                ble_batteries = asyncio.run(self._scan_bluetooth_le())
                self.devices.extend(ble_batteries)
                print(f"  Found {len(ble_batteries)} device(s)")
            except Exception as e:
                print(f"  Error: {e}")
        else:
            print("\n[3/3] Bluetooth LE scanning disabled (bleak not installed)")
        
        return self.devices
    
    def _scan_windows_battery_api(self) -> List[BatteryDevice]:
        """Scan using Windows Battery API"""
        from app_windows_battery import enumerate_batteries
        
        batteries = []
        win_batteries = enumerate_batteries()
        
        for bat in win_batteries:
            device = BatteryDevice(
                name="System Battery",
                battery_level=bat['percentage'],
                charging=bat['charging'],
                source='windows_api',
                details=bat
            )
            batteries.append(device)
        
        return batteries
    
    def _scan_hid_batteries(self) -> List[BatteryDevice]:
        """Scan HID devices and try to read battery using vendor libraries"""
        batteries = []
        
        try:
            # Get unique HID devices
            devices_dict = {}
            all_devices = hid.enumerate(0, 0)
            print(f"  Found {len(all_devices)} total HID interfaces")
            
            for device in all_devices:
                vid = device.get('vendor_id', 0)
                pid = device.get('product_id', 0)
                key = f"{vid:04x}:{pid:04x}"
                
                if key not in devices_dict:
                    devices_dict[key] = {
                        'vid': vid,
                        'pid': pid,
                        'manufacturer': device.get('manufacturer_string', ''),
                        'product': device.get('product_string', ''),
                        'path': device.get('path', b''),
                    }
            
            print(f"  Unique devices: {len(devices_dict)}")
            
            # Filter for wireless devices
            wireless_keywords = ['wireless', 'bluetooth', 'steelseries', 'logitech', 
                               'razer', 'corsair', 'mouse', 'keyboard', 'headset']
            
            wireless_devices = {
                key: dev for key, dev in devices_dict.items()
                if any(kw in dev['product'].lower() or kw in dev['manufacturer'].lower() 
                       for kw in wireless_keywords)
            }
            
            print(f"  Wireless devices: {len(wireless_devices)}")
            
            # Try to read battery from known vendors
            for key, device in wireless_devices.items():
                battery = None
                device_name = f"{device['manufacturer']} {device['product']}".strip()
                print(f"  Checking: {device_name} ({key})")
                
                # SteelSeries devices
                if device['vid'] == 0x1038:
                    print(f"    -> Trying SteelSeries protocol...")
                    battery = self._try_steelseries_battery(device)
                    if battery:
                        print(f"    -> Success!")
                    else:
                        print(f"    -> Failed")
                
                # Logitech devices
                elif device['vid'] == 0x046d:
                    print(f"    -> Trying Logitech protocol...")
                    battery = self._try_logitech_battery(device)
                
                # Razer devices
                elif device['vid'] == 0x1532:
                    print(f"    -> Trying Razer protocol...")
                    battery = self._try_razer_battery(device)
                
                # Corsair devices
                elif device['vid'] == 0x1b1c:
                    print(f"    -> Trying Corsair protocol...")
                    battery = self._try_corsair_battery(device)
                else:
                    print(f"    -> Unknown vendor, skipping")
                
                if battery:
                    batteries.append(battery)
            
        except Exception as e:
            print(f"  Error scanning HID: {e}")
            import traceback
            traceback.print_exc()
        
        return batteries
    
    def _try_steelseries_battery(self, device: Dict) -> Optional[BatteryDevice]:
        """Try to read battery from SteelSeries device"""
        try:
            import rivalcfg
            print(f"      rivalcfg imported successfully")
            
            try:
                mouse = rivalcfg.get_first_mouse()
                print(f"      get_first_mouse() returned: {mouse}")
                
                if mouse:
                    try:
                        # Use the battery property (not a method!)
                        battery_info = mouse.battery
                        print(f"      Battery info: {battery_info}")
                        
                        if battery_info and battery_info.get('level') is not None:
                            battery_level = battery_info['level']
                            is_charging = battery_info.get('is_charging', False)
                            
                            print(f"      Battery level: {battery_level}%")
                            print(f"      Charging: {is_charging}")
                            
                            mouse.close()
                            
                            return BatteryDevice(
                                name=device['product'] or f"SteelSeries {device['vid']:04x}:{device['pid']:04x}",
                                battery_level=battery_level,
                                charging=is_charging or False,
                                source='hid_steelseries',
                                details=device
                            )
                        else:
                            print(f"      Battery info not available (mouse may be off)")
                            mouse.close()
                    except AttributeError as e:
                        print(f"      AttributeError: {e}")
                        mouse.close()
                    except Exception as e:
                        print(f"      Error reading battery: {e}")
                        mouse.close()
                else:
                    print(f"      No mouse found by rivalcfg")
            except Exception as e:
                print(f"      Error calling get_first_mouse(): {e}")
                
        except ImportError:
            print(f"      rivalcfg not installed (pip install rivalcfg)")
        except Exception as e:
            print(f"      Unexpected error: {e}")
        
        return None
    
    def _try_logitech_battery(self, device: Dict) -> Optional[BatteryDevice]:
        """Try to read battery from Logitech device"""
        # Logitech uses HID++ protocol
        # Would need solaar library: pip install solaar
        try:
            # This is a placeholder - solaar has complex setup
            # For now, just return None
            pass
        except:
            pass
        
        return None
    
    def _try_razer_battery(self, device: Dict) -> Optional[BatteryDevice]:
        """Try to read battery from Razer device"""
        # Razer devices might use openrazer
        # This is Linux-focused, so skip for now
        return None
    
    def _try_corsair_battery(self, device: Dict) -> Optional[BatteryDevice]:
        """Try to read battery from Corsair device"""
        # Corsair uses CUE SDK
        # Complex setup, skip for now
        return None
    
    async def _scan_bluetooth_le(self) -> List[BatteryDevice]:
        """Scan Bluetooth LE devices for battery service"""
        batteries = []
        
        # Standard Bluetooth Battery Service UUID
        BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
        BATTERY_LEVEL_CHAR_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
        
        try:
            # Scan for BLE devices
            devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
            
            for address, (device, adv_data) in devices.items():
                # Check if device advertises battery service
                service_uuids = adv_data.service_uuids if hasattr(adv_data, 'service_uuids') else []
                
                has_battery = any(
                    uuid.lower() in [BATTERY_SERVICE_UUID.lower(), "180f"]
                    for uuid in service_uuids
                )
                
                if has_battery or True:  # Try all devices for now
                    try:
                        async with BleakClient(address, timeout=10.0) as client:
                            # Try to read battery characteristic
                            try:
                                battery_data = await client.read_gatt_char(BATTERY_LEVEL_CHAR_UUID)
                                battery_level = int.from_bytes(battery_data, byteorder='little')
                                
                                if 0 <= battery_level <= 100:
                                    device_name = adv_data.local_name or device.name or f"BLE Device {address}"
                                    
                                    batteries.append(BatteryDevice(
                                        name=device_name,
                                        battery_level=battery_level,
                                        charging=False,  # BLE doesn't always report charging
                                        source='bluetooth_le',
                                        details={'address': address}
                                    ))
                            except Exception:
                                # Device doesn't have battery characteristic
                                pass
                    except Exception:
                        # Could not connect to device
                        pass
        except Exception as e:
            print(f"  BLE scan error: {e}")
        
        return batteries


# Standalone Windows Battery module
if sys.platform == 'win32':
    import app_windows_battery
else:
    class app_windows_battery:
        @staticmethod
        def enumerate_batteries():
            return []


def main():
    if MISSING_DEPS:
        for dep in MISSING_DEPS:
            print(f"  - {dep}")
        print("\nInstall with: pip install " + " ".join(MISSING_DEPS))
    
    monitor = UniversalBatteryMonitor()
    devices = monitor.scan_all()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if not devices:
        print("\nNo battery devices found.")
    else:
        print(f"\n Found {len(devices)} battery device(s):\n")
        
        for i, device in enumerate(devices, 1):
            print(f"{i}. {device}")
            if device.details:
                for key, value in device.details.items():
                    if key not in ['device_path', 'path']:
                        print(f"     {key}: {value}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()