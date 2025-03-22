import platform
import psutil
import subprocess
import socket
import datetime
import winreg
import locale
from locale import setlocale, LC_ALL


def get_system_info():
    """Get system information."""
    return {
        "os": get_os_info(),
        "cpu": get_cpu_info(),
        "gpu": get_gpu_info(),
        "ram": get_ram_info(),
        "disks": get_disk_info(),
        "networks": get_network_info(),
        "uptime": get_system_uptime(),
        "windows_version": get_windows_version(),
        "language": get_language_info(),
    }


def get_os_info():
    """Get OS information."""
    return f"{platform.system()} {platform.release()} ({platform.version()})"


def get_cpu_info():
    """Get CPU information."""
    cpu = platform.processor()
    cpu_count = psutil.cpu_count(logical=True)
    return f"{cpu} ({cpu_count} cores)"


def get_gpu_info():
    """Get GPU information."""
    try:
        result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                               capture_output=True, text=True)
        return result.stdout.strip().split('\n')[-1].strip()
    except Exception:
        return "Unknown"


def get_ram_info():
    """Get RAM information."""
    mem = psutil.virtual_memory()
    total = mem.total // (1024 * 1024)
    available = mem.available // (1024 * 1024)
    return f"Total: {total} MB, Available: {available} MB"


def get_disk_info():
    """Get disk information."""
    partitions = psutil.disk_partitions()
    disk_info = []
    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_info.append({
                'Drive': partition.device,
                'Total': f"{usage.total // (1024 * 1024 * 1024)} GB",
                'Used': f"{usage.used // (1024 * 1024 * 1024)} GB",
                'Free': f"{usage.free // (1024 * 1024 * 1024)} GB",
                'Percent': f"{usage.percent}%"
            })
        except PermissionError:
            continue
    return disk_info


def get_network_info():
    """Get network information."""
    net_info = []
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                net_info.append({
                    'Interface': interface,
                    'IP Address': addr.address,
                    'Netmask': addr.netmask
                })
    return net_info


def get_system_uptime():
    """Get system uptime."""
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    current_time = datetime.datetime.now()
    uptime = current_time - boot_time
    return str(uptime).split('.')[0]


def get_windows_version():
    """Get Windows version."""
    if platform.system() != 'Windows':
        return "N/A (Not Windows)"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        release_id = winreg.QueryValueEx(key, "ReleaseId")[0]
        current_version = winreg.QueryValueEx(key, "CurrentVersion")[0]
        return f"Windows 10 Version {release_id} (Build {current_version})"
    except Exception:
        return "Unknown Windows Version"


def get_language_info():
    """Get language information."""
    try:
        setlocale(LC_ALL, '')
        return locale.getlocale()[0]
    except Exception:
        return "Unknown"


def format_network_info(info):
    """Format network information."""
    formatted = []
    for item in info:
        formatted.append(f"{item['Interface']}: {item['IP Address']} ({item['Netmask']})")
    return formatted


def format_disk_info(info):
    """Format disk information."""
    formatted = []
    for item in info:
        formatted.append(f"{item['Drive']}: {item['Total']}, Used: {item['Used']}, Free: {item['Free']}, {item['Percent']}")
    return formatted


if __name__ == "__main__":
    # Get all system information
    info = get_system_info()
    print("\n=== System Information ===")
    print(f"Operating System: {info['os']}")
    print(f"Windows Version: {info['windows_version']}")
    print(f"Language: {info['language']}")
    print(f"\nCPU: {info['cpu']}")
    print(f"GPU: {info['gpu']}")
    print(f"RAM: {info['ram']}")
    print("\nDisk Information:")
    for disk in format_disk_info(info['disks']):
        print(f"  {disk}")
    print("\nNetwork Information:")
    for network in format_network_info(info['networks']):
        print(f"  {network}")
    print(f"\nSystem Uptime: {info['uptime']}")
