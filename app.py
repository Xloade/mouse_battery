import sys
from typing import List, Dict, Optional
import rivalcfg
import time
from parser import detect_windows_devices

# Check dependencies
MISSING_DEPS = []

try:
    import hid
except ImportError:
    MISSING_DEPS.append("hidapi")

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
    
    def scan_specific_device(self, vid: int, pid: int) -> Optional[BatteryDevice]:
        """
        Scan for a specific device by VID/PID only (much faster than scan_all)
        Returns the BatteryDevice or None if not found
        """
        try:
            # Use cached device classification
            classified_devices = detect_windows_devices(use_cache=True, cache_timeout=30)
            
            # Check if this specific device exists
            key = (vid, pid)
            if key not in classified_devices:
                return None
            
            interfaces = classified_devices[key]
            
            # Combine capabilities
            combined_caps = {
                "mouse": False,
                "keyboard": False,
                "gamepad": False,
                "consumer_control": False,
                "digitizer": False,
            }
            
            for interface in interfaces:
                caps = interface["capabilities"]
                for k in combined_caps:
                    combined_caps[k] |= caps[k]
            
            # Check if it's a battery candidate
            is_candidate = combined_caps["mouse"] or combined_caps["gamepad"]
            
            if not is_candidate:
                return None
            
            # Get device details
            device_info = self._get_device_details(vid, pid)
            if not device_info:
                return None
            
            candidate = {
                'vid': vid,
                'pid': pid,
                'capabilities': combined_caps,
                'device_info': device_info
            }
            
            # Try to read battery based on vendor
            battery = None
            
            if vid == 0x1038:  # SteelSeries
                battery = self._try_steelseries_battery(candidate)
            elif vid == 0x046d:  # Logitech
                battery = self._try_logitech_battery(candidate)
            elif vid == 0x1532:  # Razer
                battery = self._try_razer_battery(candidate)
            elif vid == 0x1b1c:  # Corsair
                battery = self._try_corsair_battery(candidate)
            
            if not battery:
                battery = self._try_generic_hid_battery(candidate)
            
            return battery
            
        except Exception as e:
            print(f"  Error scanning device {vid:04x}:{pid:04x}: {e}")
            return None
    
    def _scan_hid_batteries(self) -> List[BatteryDevice]:
        batteries = []
        try:
            # Use parser to detect and classify HID devices
            print("  Detecting HID devices using parser...")
            classified_devices = detect_windows_devices(use_cache=True, cache_timeout=30)
            print(f"  Found {len(classified_devices)} unique devices")
            
            # Filter for devices that are likely to be wireless and have batteries
            # Focus on mice and gamepads (keyboards typically don't report battery via HID)
            wireless_candidates = []
            
            for (vid, pid), interfaces in classified_devices.items():
                # Combine capabilities from all interfaces
                combined_caps = {
                    "mouse": False,
                    "keyboard": False,
                    "gamepad": False,
                    "consumer_control": False,
                    "digitizer": False,
                }
                
                for interface in interfaces:
                    caps = interface["capabilities"]
                    for key in combined_caps:
                        combined_caps[key] |= caps[key]
                
                # Check if device is a mouse or gamepad (likely candidates for wireless with battery)
                is_candidate = combined_caps["mouse"] or combined_caps["gamepad"]
                
                if is_candidate:
                    # Get device details from HID
                    device_info = self._get_device_details(vid, pid)
                    if device_info:
                        # Additional check: look for wireless indicators
                        product = device_info.get('product_string', '').lower()
                        manufacturer = device_info.get('manufacturer_string', '').lower()
                        
                        is_wireless = any(keyword in product or keyword in manufacturer 
                                        for keyword in ['wireless', 'bluetooth', 'bt'])
                        
                        # For known brands, assume wireless if it's a mouse/gamepad
                        known_wireless_vendors = [
                            0x1038,  # SteelSeries
                            0x046d,  # Logitech
                            0x1532,  # Razer
                            0x1b1c,  # Corsair
                            0x045e,  # Microsoft
                        ]
                        is_known_vendor = vid in known_wireless_vendors
                        
                        if is_wireless or (is_known_vendor and combined_caps["mouse"]):
                            wireless_candidates.append({
                                'vid': vid,
                                'pid': pid,
                                'capabilities': combined_caps,
                                'device_info': device_info
                            })
            
            print(f"  Wireless candidates: {len(wireless_candidates)}")
            
            # Try to read battery from wireless devices
            for candidate in wireless_candidates:
                device_name = f"{candidate['device_info'].get('manufacturer_string', '')} " \
                            f"{candidate['device_info'].get('product_string', '')}".strip()
                
                if not device_name:
                    device_name = f"Device {candidate['vid']:04x}:{candidate['pid']:04x}"
                
                print(f"  Checking: {device_name}")
                
                battery = None
                
                # SteelSeries devices
                if candidate['vid'] == 0x1038:
                    battery = self._try_steelseries_battery(candidate)
                
                # Razer devices
                elif candidate['vid'] == 0x1532:
                    battery = self._try_razer_battery(candidate)
    
                if battery:
                    batteries.append(battery)
            
        except Exception as e:
            print(f"  Error scanning HID: {e}")
            import traceback
            traceback.print_exc()
        
        return batteries
    
    def _get_device_details(self, vid: int, pid: int) -> Optional[Dict]:
        """Get detailed device information from HID enumerate"""
        try:
            for device in hid.enumerate(vid, pid):
                # Return the first matching device
                return {
                    'path': device.get('path', b''),
                    'vendor_id': device.get('vendor_id', 0),
                    'product_id': device.get('product_id', 0),
                    'serial_number': device.get('serial_number', ''),
                    'manufacturer_string': device.get('manufacturer_string', ''),
                    'product_string': device.get('product_string', ''),
                    'interface_number': device.get('interface_number', -1),
                }
        except Exception as e:
            print(f"    Error getting device details: {e}")
        return None
    
    def _try_steelseries_battery(self, candidate: Dict) -> Optional[BatteryDevice]:
        """Try to read battery level from SteelSeries device"""
        device_info = candidate['device_info']
        
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
                                
                                device_name = device_info.get('product_string', '') or \
                                            f"SteelSeries {candidate['vid']:04x}:{candidate['pid']:04x}"
                                
                                result = BatteryDevice(
                                    name=device_name,
                                    battery_level=battery_level,
                                    charging=is_charging or False,
                                    source='hid_steelseries',
                                    details={
                                        'vid': candidate['vid'],
                                        'pid': candidate['pid'],
                                        'capabilities': candidate['capabilities'],
                                        'manufacturer': device_info.get('manufacturer_string', ''),
                                        'product': device_info.get('product_string', '')
                                    }
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
    
    def _try_razer_battery(self, candidate: Dict) -> Optional[BatteryDevice]:
        """Try to read battery level from Razer device"""
        device_info = candidate['device_info']
        device_name = device_info.get('product_string', '') or \
                     f"Razer {candidate['vid']:04x}:{candidate['pid']:04x}"
        
        # Try OpenRazer first (Linux)
        try:
            import openrazer.client
            
            print(f"      Attempting OpenRazer battery query...")
            
            device_manager = openrazer.client.DeviceManager()
            
            # Find matching device by VID/PID or name
            for device in device_manager.devices:
                if device.has("battery"):
                    # Check if this is our device
                    device_serial = device.serial
                    our_serial = device_info.get('serial_number', '')
                    
                    # If serial matches or we only have one Razer device, use it
                    if not our_serial or device_serial == our_serial or len(device_manager.devices) == 1:
                        battery_level = device.battery_level
                        is_charging = device.is_charging if hasattr(device, 'is_charging') else False
                        
                        print(f"      Battery level: {battery_level}%")
                        print(f"      Charging: {is_charging}")
                        
                        return BatteryDevice(
                            name=device_name,
                            battery_level=battery_level,
                            charging=is_charging,
                            source='openrazer',
                            details={
                                'vid': candidate['vid'],
                                'pid': candidate['pid'],
                                'capabilities': candidate['capabilities'],
                                'manufacturer': device_info.get('manufacturer_string', ''),
                                'product': device_info.get('product_string', ''),
                                'serial': device_serial
                            }
                        )
            
            print(f"      No matching Razer device found in OpenRazer")
            
        except ImportError:
            print(f"      OpenRazer library not available, trying direct HID access...")
            # Fall back to direct HID protocol
            return self._try_razer_battery_hid(candidate, device_info, device_name)
        except Exception as e:
            print(f"      OpenRazer error: {e}, trying direct HID access...")
            return self._try_razer_battery_hid(candidate, device_info, device_name)
        
        return None
    
    def _try_razer_battery_hid(self, candidate: Dict, device_info: Dict, device_name: str) -> Optional[BatteryDevice]:
        """Try to read battery from Razer device using direct HID protocol"""
        try:
            device = hid.device()
            device.open(candidate['vid'], candidate['pid'])
            
            print(f"      Attempting Razer HID battery query...")
            
            # Razer protocol: Send battery query command
            # Command structure: [0x00, transaction_id, 0x00, 0x00, 0x00, command, subcommand, ...]
            # Battery query: command=0x07 (misc), subcommand=0x80 (battery)
            
            # Build the command packet
            transaction_id = 0xFF
            command = [0x00] * 90  # Razer uses 90-byte packets
            command[0] = 0x00  # Status
            command[1] = transaction_id  # Transaction ID
            command[2] = 0x00  # Reserved
            command[3] = 0x00  # Reserved
            command[4] = 0x00  # Reserved
            command[5] = 0x02  # Data size (2 bytes for battery query)
            command[6] = 0x07  # Command class: Misc
            command[7] = 0x80  # Command ID: Battery level
            
            # Calculate CRC (XOR of bytes 2-88)
            crc = 0
            for i in range(2, 88):
                crc ^= command[i]
            command[88] = crc
            
            try:
                # Send the command
                device.write([0x00] + command)  # Add report ID
                time.sleep(0.1)
                
                # Read response
                response = device.read(90, timeout_ms=500)
                
                if response and len(response) >= 9:
                    # Check if response is valid
                    if response[6] == 0x07 and response[7] == 0x80:
                        # Battery level is in byte 9 (0-255, convert to percentage)
                        battery_raw = response[9] if len(response) > 9 else 0
                        battery_level = int((battery_raw / 255.0) * 100)
                        
                        # Charging status might be in byte 10
                        is_charging = response[10] == 0x01 if len(response) > 10 else False
                        
                        if 0 <= battery_level <= 100:
                            print(f"      Battery level: {battery_level}%")
                            print(f"      Charging: {is_charging}")
                            
                            device.close()
                            
                            return BatteryDevice(
                                name=device_name,
                                battery_level=battery_level,
                                charging=is_charging,
                                source='hid_razer',
                                details={
                                    'vid': candidate['vid'],
                                    'pid': candidate['pid'],
                                    'capabilities': candidate['capabilities'],
                                    'manufacturer': device_info.get('manufacturer_string', ''),
                                    'product': device_info.get('product_string', '')
                                }
                            )
                    else:
                        print(f"      Invalid Razer response")
                else:
                    print(f"      No response from Razer device")
                    
            except Exception as e:
                print(f"      Razer HID protocol error: {e}")
            
            device.close()
            
        except Exception as e:
            print(f"      Error opening Razer device: {e}")
        
        return None

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