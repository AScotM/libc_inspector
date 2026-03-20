#!/usr/bin/env python3

import ctypes
import platform
import os
from datetime import datetime

class SysInfo(ctypes.Structure):
    _fields_ = [
        ("uptime", ctypes.c_long),
        ("loads", ctypes.c_ulong * 3),
        ("totalram", ctypes.c_ulong),
        ("freeram", ctypes.c_ulong),
        ("sharedram", ctypes.c_ulong),
        ("bufferram", ctypes.c_ulong),
        ("totalswap", ctypes.c_ulong),
        ("freeswap", ctypes.c_ulong),
        ("procs", ctypes.c_ushort),
        ("totalhigh", ctypes.c_ulong),
        ("freehigh", ctypes.c_ulong),
        ("mem_unit", ctypes.c_uint)
    ]

class RLimit(ctypes.Structure):
    _fields_ = [
        ("rlim_cur", ctypes.c_ulong),
        ("rlim_max", ctypes.c_ulong)
    ]

class LibcInspector:
    def __init__(self):
        self.libc = None
        self.libc_available = False
    
    def load(self):
        libc_names = {
            'Linux': 'libc.so.6',
            'Darwin': 'libc.dylib',
            'Windows': 'msvcrt.dll'
        }
        try:
            libc_name = libc_names.get(platform.system(), 'libc.so.6')
            self.libc = ctypes.CDLL(libc_name)
            self.libc_available = True
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load libc: {e}")
            self.libc_available = False
            return False
    
    def get_pid(self):
        if not self.libc_available:
            return None
        try:
            self.libc.getpid.argtypes = []
            self.libc.getpid.restype = ctypes.c_int
            return self.libc.getpid()
        except AttributeError:
            return None
    
    def get_ppid(self):
        if not self.libc_available:
            return None
        try:
            self.libc.getppid.argtypes = []
            self.libc.getppid.restype = ctypes.c_int
            return self.libc.getppid()
        except AttributeError:
            return None
    
    def get_time(self):
        if not self.libc_available:
            return None
        try:
            self.libc.time.argtypes = [ctypes.c_void_p]
            self.libc.time.restype = ctypes.c_long
            return self.libc.time(None)
        except AttributeError:
            return None
    
    def get_uid(self):
        if not self.libc_available:
            return None
        try:
            self.libc.getuid.argtypes = []
            self.libc.getuid.restype = ctypes.c_uint
            return self.libc.getuid()
        except AttributeError:
            return None
    
    def get_gid(self):
        if not self.libc_available:
            return None
        try:
            self.libc.getgid.argtypes = []
            self.libc.getgid.restype = ctypes.c_uint
            return self.libc.getgid()
        except AttributeError:
            return None
    
    def get_hostname(self):
        if not self.libc_available:
            return None
        try:
            self.libc.gethostname.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
            self.libc.gethostname.restype = ctypes.c_int
            buf = ctypes.create_string_buffer(256)
            if self.libc.gethostname(buf, 256) == 0:
                return buf.value.decode()
            return None
        except AttributeError:
            return None
    
    def get_loadavg(self):
        if not self.libc_available:
            return None
        try:
            self.libc.getloadavg.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
            self.libc.getloadavg.restype = ctypes.c_int
            loadavg = (ctypes.c_double * 3)()
            if self.libc.getloadavg(loadavg, 3) == 3:
                return (loadavg[0], loadavg[1], loadavg[2])
            return None
        except AttributeError:
            return None
    
    def get_sysinfo(self):
        if platform.system() != 'Linux' or not self.libc_available:
            return None
        try:
            self.libc.sysinfo.argtypes = [ctypes.POINTER(SysInfo)]
            self.libc.sysinfo.restype = ctypes.c_int
            si = SysInfo()
            if self.libc.sysinfo(ctypes.byref(si)) == 0:
                mem_unit = si.mem_unit if si.mem_unit else 1
                return {
                    "uptime": si.uptime,
                    "totalram": si.totalram * mem_unit,
                    "freeram": si.freeram * mem_unit,
                    "totalswap": si.totalswap * mem_unit,
                    "freeswap": si.freeswap * mem_unit,
                    "procs": si.procs
                }
            return None
        except (AttributeError, TypeError):
            return None
    
    def get_rlimit(self, resource):
        if not self.libc_available:
            return None
        try:
            self.libc.getrlimit.argtypes = [ctypes.c_int, ctypes.POINTER(RLimit)]
            self.libc.getrlimit.restype = ctypes.c_int
            rlim = RLimit()
            if self.libc.getrlimit(resource, ctypes.byref(rlim)) == 0:
                return (rlim.rlim_cur, rlim.rlim_max)
            return None
        except (AttributeError, TypeError):
            return None
    
    def collect(self):
        data = {
            "pid": self.get_pid(),
            "ppid": self.get_ppid(),
            "uid": self.get_uid(),
            "gid": self.get_gid(),
            "epoch_time": self.get_time(),
            "hostname": self.get_hostname(),
            "loadavg": self.get_loadavg(),
            "sysinfo": self.get_sysinfo()
        }
        
        if self.libc_available:
            try:
                import resource
                data["rlimit_nofile"] = self.get_rlimit(resource.RLIMIT_NOFILE)
            except (ImportError, AttributeError):
                data["rlimit_nofile"] = None
        
        return data

def print_header():
    print("=" * 60)
    print(" Advanced Libc Inspector")
    print("=" * 60)

def print_system_info():
    print("\n[System Information]")
    print(f"OS           : {platform.system()} {platform.release()}")
    print(f"Architecture : {platform.machine()}")
    print(f"Python       : {platform.python_version()}")
    if hasattr(platform, 'node'):
        print(f"Hostname     : {platform.node()}")

def format_bytes(bytes_value):
    if bytes_value is None:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def format_uptime(seconds):
    if seconds is None:
        return "N/A"
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    return f"{days}d {hours}h {minutes}m"

def print_libc_info(data):
    print("\n[Process Information]")
    pid_val = data['pid'] if data['pid'] is not None else "N/A"
    print(f"Process ID   : {pid_val}")
    if hasattr(os, 'getpid'):
        print(f"Python PID   : {os.getpid()}")
    
    ppid_val = data['ppid'] if data['ppid'] is not None else "N/A"
    print(f"Parent PID   : {ppid_val}")
    
    uid_val = data['uid'] if data['uid'] is not None else "N/A"
    print(f"User ID      : {uid_val}")
    if hasattr(os, 'getuid'):
        print(f"Python UID   : {os.getuid()}")
    
    gid_val = data['gid'] if data['gid'] is not None else "N/A"
    print(f"Group ID     : {gid_val}")
    if hasattr(os, 'getgid'):
        print(f"Python GID   : {os.getgid()}")
    
    if data['loadavg'] is not None:
        print("\n[System Load]")
        print(f"Load average : {data['loadavg'][0]:.2f}, {data['loadavg'][1]:.2f}, {data['loadavg'][2]:.2f}")
    
    if data['epoch_time'] is not None:
        print("\n[Time Information]")
        print(f"Epoch time   : {data['epoch_time']}")
        print(f"Readable time: {datetime.fromtimestamp(data['epoch_time']).strftime('%Y-%m-%d %H:%M:%S')}")
    
    if data['sysinfo'] is not None:
        print("\n[Memory Information]")
        print(f"Uptime       : {format_uptime(data['sysinfo']['uptime'])}")
        print(f"Total RAM    : {format_bytes(data['sysinfo']['totalram'])}")
        print(f"Free RAM     : {format_bytes(data['sysinfo']['freeram'])}")
        print(f"Total Swap   : {format_bytes(data['sysinfo']['totalswap'])}")
        print(f"Free Swap    : {format_bytes(data['sysinfo']['freeswap'])}")
        print(f"Processes    : {data['sysinfo']['procs']}")
    
    if data['rlimit_nofile'] is not None:
        print("\n[Resource Limits]")
        print(f"Max open files: soft={data['rlimit_nofile'][0]}, hard={data['rlimit_nofile'][1]}")
    
    if data['hostname'] is not None:
        print("\n[Host Information]")
        print(f"Hostname     : {data['hostname']}")

def print_comparison():
    print("\n[Python Standard Library Equivalents]")
    
    if hasattr(os, 'getpid'):
        print(f"os.getpid()          : {os.getpid()}")
    if hasattr(os, 'getppid'):
        print(f"os.getppid()         : {os.getppid()}")
    if hasattr(os, 'getuid'):
        print(f"os.getuid()          : {os.getuid()}")
    if hasattr(os, 'getgid'):
        print(f"os.getgid()          : {os.getgid()}")
    if hasattr(os, 'uname'):
        uname_info = os.uname()
        print(f"os.uname().nodename  : {uname_info.nodename}")
    if hasattr(os, 'getloadavg'):
        try:
            loadavg = os.getloadavg()
            print(f"os.getloadavg()      : {loadavg[0]:.2f}, {loadavg[1]:.2f}, {loadavg[2]:.2f}")
        except OSError:
            print(f"os.getloadavg()      : Not available on this platform")

def main():
    print_header()
    print_system_info()
    
    inspector = LibcInspector()
    
    if not inspector.load():
        print("\n[WARNING] Running in limited mode with Python fallbacks only")
    
    data = inspector.collect()
    print_libc_info(data)
    
    print("\n" + "=" * 60)
    print_comparison()
    
    print("\n[Note]")
    print("This tool demonstrates direct libc interaction via ctypes.")
    print("Values obtained through libc should match Python standard library equivalents.")
    print("Some features may be platform-specific (Linux sysinfo, etc.)")
    print("None values indicate the function is unavailable on this platform.")

if __name__ == "__main__":
    main()
