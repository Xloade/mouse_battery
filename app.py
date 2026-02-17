import sys
from typing import List, Dict, Optional
import rivalcfg
import time

# Check dependencies
MISSING_DEPS = []

try:
    import hid
except ImportError:
    MISSING_DEPS.append("hidapi")

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
    def __init__(self):
        self.devices: List[BatteryDevice] = []
    
    def scan_all(self) -> List[BatteryDevice]:
        self.devices = []
        try:
            hid_batteries = self._scan_hid_batteries()
            self.devices.extend(hid_batteries)
            print(f"  Found {len(hid_batteries)} device(s)")
        except Exception as e:
            print(f"  Error: {e}")
        
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
            wireless_keywords = ['wireless', 'bluetooth', 'steelseries', 'mouse',]
            
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
                    battery = self._try_steelseries_battery(device)
                if battery:
                    batteries.append(battery)
            
        except Exception as e:
            print(f"  Error scanning HID: {e}")
            import traceback
            traceback.print_exc()
        
        return batteries
    
    def _try_steelseries_battery(self, device: Dict) -> Optional[BatteryDevice]:
        for attempt in range(3):
            mouse = None
            try:
                if attempt > 0:
                    print(f"      Retry attempt {attempt + 1}...")
                    time.sleep(1.0)  # Wait longer before retry    
            
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
                                
                                result = BatteryDevice(
                                    name=device['product'] or f"SteelSeries {device['vid']:04x}:{device['pid']:04x}",
                                    battery_level=battery_level,
                                    charging=is_charging or False,
                                    source='hid_steelseries',
                                    details=device
                                )
                                
                                mouse.close()
                                time.sleep(0.2)  # Give device time to release
                                
                                return result
                            else:
                                print(f"      Battery info not available, will retry...")
                                mouse.close()
                                time.sleep(0.5)  # Give device time to release
                                continue  # Retry on next attempt
                        except AttributeError as e:
                            print(f"      AttributeError: {e}")
                            if mouse:
                                mouse.close()
                                time.sleep(0.5)
                            continue  # Retry on next attempt
                        except Exception as e:
                            print(f"      Error reading battery: {e}")
                            if mouse:
                                mouse.close()
                                time.sleep(0.5)
                            continue  # Retry on next attempt
                    else:
                        print(f"      No mouse found by rivalcfg")
                        time.sleep(0.5)
                        continue  # Retry on next attempt
                except Exception as e:
                    print(f"      Error calling get_first_mouse(): {e}")
                    if mouse:
                        try:
                            mouse.close()
                        except:
                            pass
                        time.sleep(0.5)
                    continue  # Retry on next attempt
            except Exception as e:
                print(f"      Error on attempt {attempt + 1}: {e}")
                if mouse:
                    try:
                        mouse.close()
                    except:
                        pass
                time.sleep(1.0)
                continue
            return None

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


if __name__ == "__main__":
    main()