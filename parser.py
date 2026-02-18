from typing import Dict
import hid


# Cache for device detection results
_device_cache = None
_cache_timestamp = 0


def classify_device(app_collections) -> Dict[str, bool]:
    capabilities = {
        "mouse": False,
        "keyboard": False,
        "gamepad": False,
        "consumer_control": False,
        "digitizer": False,
    }

    for usage_page, usage in app_collections:
        if usage_page == 0x01:  # Generic Desktop
            if usage == 0x02:
                capabilities["mouse"] = True
            elif usage == 0x06:
                capabilities["keyboard"] = True
            elif usage == 0x05:
                capabilities["gamepad"] = True

        elif usage_page == 0x0C:  # Consumer
            capabilities["consumer_control"] = True

        elif usage_page == 0x0D:  # Digitizer
            capabilities["digitizer"] = True

    return capabilities

def classify_usage(usage_page, usage):
    caps = {
        "mouse": False,
        "keyboard": False,
        "gamepad": False,
        "consumer_control": False,
        "digitizer": False,
    }

    if usage_page == 0x01:  # Generic Desktop
        if usage == 0x02:
            caps["mouse"] = True
        elif usage == 0x06:
            caps["keyboard"] = True
        elif usage == 0x05:
            caps["gamepad"] = True

    elif usage_page == 0x0C:
        caps["consumer_control"] = True

    elif usage_page == 0x0D:
        caps["digitizer"] = True

    return caps

def detect_windows_devices(use_cache=True, cache_timeout=10):
    """
    Detect HID devices on Windows.
    
    Args:
        use_cache: If True, use cached results if available and not expired
        cache_timeout: Cache validity in seconds (default 60)
    
    Returns:
        Dictionary of devices keyed by (vendor_id, product_id)
    """
    global _device_cache, _cache_timestamp
    
    import time
    current_time = time.time()
    
    # Return cached results if valid
    if use_cache and _device_cache is not None:
        if (current_time - _cache_timestamp) < cache_timeout:
            return _device_cache
    
    results = {}
    
    for device_info in hid.enumerate():
        # Get usage info directly from enumerate (no need to open device)
        usage_page = device_info.get('usage_page', 0)
        usage = device_info.get('usage', 0)
        
        # Skip devices without valid usage info
        if usage_page == 0 and usage == 0:
            continue
            
        caps = classify_usage(usage_page, usage)
        
        key = (device_info['vendor_id'], device_info['product_id'])
        if key not in results:
            results[key] = []

        results[key].append({
            "usage_page": usage_page,
            "usage": usage,
            "capabilities": caps
        })
    
    # Update cache
    _device_cache = results
    _cache_timestamp = current_time

    return results


if __name__ == "__main__":
    import time
    start = time.time()
    
    devices = detect_windows_devices(use_cache=False)  # Force fresh scan for demo
    
    elapsed = time.time() - start
    print(f"Scan completed in {elapsed:.2f} seconds\n")

    for (vid, pid), interfaces in devices.items():
        print(f"\nDevice VID={hex(vid)} PID={hex(pid)}")

        combined = {
            "mouse": False,
            "keyboard": False,
            "gamepad": False,
            "consumer_control": False,
            "digitizer": False,
        }

        for iface in interfaces:
            for k in combined:
                combined[k] |= iface["capabilities"][k]

        print("Capabilities:", combined)
