import ctypes
from ctypes import wintypes

# Constants
BATTERY_SYSTEM_BATTERY = 0x80000000
BATTERY_POWER_ON_LINE = 0x00000001

DIGCF_PRESENT = 0x00000002
DIGCF_DEVICEINTERFACE = 0x00000010

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3

IOCTL_BATTERY_QUERY_TAG = 0x00294040
IOCTL_BATTERY_QUERY_INFORMATION = 0x00294044
IOCTL_BATTERY_QUERY_STATUS = 0x0029404C

INVALID_HANDLE_VALUE = -1

# GUID Structure
class GUID(ctypes.Structure):
    _fields_ = [
        ('Data1', wintypes.DWORD),
        ('Data2', wintypes.WORD),
        ('Data3', wintypes.WORD),
        ('Data4', wintypes.BYTE * 8),
    ]

# GUID_DEVCLASS_BATTERY
GUID_BATTERY = GUID()
GUID_BATTERY.Data1 = 0x72CEC4C4
GUID_BATTERY.Data2 = 0xE325
GUID_BATTERY.Data3 = 0x11D0
GUID_BATTERY.Data4 = (wintypes.BYTE * 8)(0xB9, 0xC0, 0x00, 0xA0, 0xC9, 0x05, 0x77, 0x25)

# Structures
class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('InterfaceClassGuid', GUID),
        ('Flags', wintypes.DWORD),
        ('Reserved', ctypes.POINTER(ctypes.c_ulong)),
    ]

class SP_DEVICE_INTERFACE_DETAIL_DATA(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('DevicePath', ctypes.c_wchar * 256),
    ]

class BATTERY_QUERY_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('BatteryTag', wintypes.ULONG),
        ('InformationLevel', wintypes.LONG),
        ('AtRate', wintypes.LONG),
    ]

class BATTERY_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('Capabilities', wintypes.ULONG),
        ('Technology', wintypes.CHAR),
        ('Reserved', wintypes.CHAR * 3),
        ('Chemistry', wintypes.CHAR * 4),
        ('DesignedCapacity', wintypes.ULONG),
        ('FullChargedCapacity', wintypes.ULONG),
        ('DefaultAlert1', wintypes.ULONG),
        ('DefaultAlert2', wintypes.ULONG),
        ('CriticalBias', wintypes.ULONG),
        ('CycleCount', wintypes.ULONG),
    ]

class BATTERY_WAIT_STATUS(ctypes.Structure):
    _fields_ = [
        ('BatteryTag', wintypes.ULONG),
        ('Timeout', wintypes.ULONG),
        ('PowerState', wintypes.ULONG),
        ('LowCapacity', wintypes.ULONG),
        ('HighCapacity', wintypes.ULONG),
    ]

class BATTERY_STATUS(ctypes.Structure):
    _fields_ = [
        ('PowerState', wintypes.ULONG),
        ('Capacity', wintypes.ULONG),
        ('Voltage', wintypes.ULONG),
        ('Rate', wintypes.LONG),
    ]

# Load Windows APIs
setupapi = ctypes.WinDLL('setupapi', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Function prototypes
SetupDiGetClassDevs = setupapi.SetupDiGetClassDevsA
SetupDiGetClassDevs.argtypes = [
    ctypes.POINTER(GUID),
    wintypes.LPCSTR,
    wintypes.HWND,
    wintypes.DWORD
]
SetupDiGetClassDevs.restype = wintypes.HANDLE

SetupDiEnumDeviceInterfaces = setupapi.SetupDiEnumDeviceInterfaces
SetupDiEnumDeviceInterfaces.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.POINTER(GUID),
    wintypes.DWORD,
    ctypes.POINTER(SP_DEVICE_INTERFACE_DATA)
]
SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL

SetupDiGetDeviceInterfaceDetail = setupapi.SetupDiGetDeviceInterfaceDetailW
SetupDiGetDeviceInterfaceDetail.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(SP_DEVICE_INTERFACE_DATA),
    ctypes.POINTER(SP_DEVICE_INTERFACE_DETAIL_DATA),
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.c_void_p
]
SetupDiGetDeviceInterfaceDetail.restype = wintypes.BOOL

SetupDiDestroyDeviceInfoList = setupapi.SetupDiDestroyDeviceInfoList
SetupDiDestroyDeviceInfoList.argtypes = [wintypes.HANDLE]
SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL

CreateFile = kernel32.CreateFileW
CreateFile.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE
]
CreateFile.restype = wintypes.HANDLE

DeviceIoControl = kernel32.DeviceIoControl
DeviceIoControl.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.c_void_p
]
DeviceIoControl.restype = wintypes.BOOL

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

def get_battery_info(device_path):
    
    h_battery = CreateFile(
        device_path,
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        0,
        None
    )
    
    if h_battery == INVALID_HANDLE_VALUE:
        return None
    
    try:
        battery_tag = wintypes.ULONG(0)
        dw_out = wintypes.DWORD()
        dw_wait = wintypes.DWORD(0)
        
        if not DeviceIoControl(
            h_battery,
            IOCTL_BATTERY_QUERY_TAG,
            ctypes.byref(dw_wait),
            ctypes.sizeof(dw_wait),
            ctypes.byref(battery_tag),
            ctypes.sizeof(battery_tag),
            ctypes.byref(dw_out),
            None
        ):
            return None
        
        if battery_tag.value == 0:
            return None
        
        bqi = BATTERY_QUERY_INFORMATION()
        bqi.BatteryTag = battery_tag.value
        bqi.InformationLevel = 0
        
        bi = BATTERY_INFORMATION()
        
        if not DeviceIoControl(
            h_battery,
            IOCTL_BATTERY_QUERY_INFORMATION,
            ctypes.byref(bqi),
            ctypes.sizeof(bqi),
            ctypes.byref(bi),
            ctypes.sizeof(bi),
            ctypes.byref(dw_out),
            None
        ):
            return None
        
        if not (bi.Capabilities & BATTERY_SYSTEM_BATTERY):
            return None
        
        bws = BATTERY_WAIT_STATUS()
        bws.BatteryTag = battery_tag.value
        
        bs = BATTERY_STATUS()
        
        if not DeviceIoControl(
            h_battery,
            IOCTL_BATTERY_QUERY_STATUS,
            ctypes.byref(bws),
            ctypes.sizeof(bws),
            ctypes.byref(bs),
            ctypes.sizeof(bs),
            ctypes.byref(dw_out),
            None
        ):
            return None
        
        if bi.FullChargedCapacity == 0:
            percentage = 0
        else:
            percentage = (bs.Capacity * 100) // bi.FullChargedCapacity
        
        is_charging = bool(bs.PowerState & BATTERY_POWER_ON_LINE)
        chemistry = bi.Chemistry[:4].decode('ascii', errors='ignore').strip('\x00')
        
        return {
            'percentage': percentage,
            'charging': is_charging,
            'device_path': device_path
        }
        
    finally:
        CloseHandle(h_battery)

def enumerate_batteries():
    
    batteries = []
    
    h_dev = SetupDiGetClassDevs(
        ctypes.byref(GUID_BATTERY),
        None,
        None,
        DIGCF_PRESENT | DIGCF_DEVICEINTERFACE
    )
    
    if h_dev == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())
    
    try:
        for i in range(10):
            did = SP_DEVICE_INTERFACE_DATA()
            did.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)
            
            if not SetupDiEnumDeviceInterfaces(
                h_dev,
                None,
                ctypes.byref(GUID_BATTERY),
                i,
                ctypes.byref(did)
            ):
                break
            
            required_size = wintypes.DWORD()
            SetupDiGetDeviceInterfaceDetail(
                h_dev,
                ctypes.byref(did),
                None,
                0,
                ctypes.byref(required_size),
                None
            )
            
            pdidd = SP_DEVICE_INTERFACE_DETAIL_DATA()
            pdidd.cbSize = ctypes.sizeof(ctypes.c_ulong) + ctypes.sizeof(ctypes.c_wchar)
            
            if SetupDiGetDeviceInterfaceDetail(
                h_dev,
                ctypes.byref(did),
                ctypes.byref(pdidd),
                ctypes.sizeof(pdidd),
                ctypes.byref(required_size),
                None
            ):
                info = get_battery_info(pdidd.DevicePath)
                if info:
                    batteries.append(info)
        
    finally:
        SetupDiDestroyDeviceInfoList(h_dev)
    
    return batteries
