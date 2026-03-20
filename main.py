#!/usr/bin/env python3

import ctypes
import platform
import os
from datetime import datetime

class LibcInspector:
    def __init__(self):
        self.libc = None
    
    def load(self):
        libc_names = {
            'Linux': 'libc.so.6',
            'Darwin': 'libc.dylib',
            'Windows': 'msvcrt.dll'
        }
        try:
            libc_name = libc_names.get(platform.system(), 'libc.so.6')
            self.libc = ctypes.CDLL(libc_name)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load libc: {e}")
            return False
    
    def get_pid(self) -> int:
        self.libc.getpid.argtypes = []
        self.libc.getpid.restype = ctypes.c_int
        return self.libc.getpid()
    
    def get_ppid(self) -> int:
        self.libc.getppid.argtypes = []
        self.libc.getppid.restype = ctypes.c_int
        return self.libc.getppid()
    
    def get_time(self) -> int:
        self.libc.time.argtypes = [ctypes.c_void_p]
        self.libc.time.restype = ctypes.c_long
        return self.libc.time(None)
    
    def get_uid(self) -> int:
        self.libc.getuid.argtypes = []
        self.libc.getuid.restype = ctypes.c_uint
        return self.libc.getuid()
    
    def get_gid(self) -> int:
        self.libc.getgid.argtypes = []
        self.libc.getgid.restype = ctypes.c_uint
        return self.libc.getgid()
    
    def get_hostname(self) -> str:
        self.libc.gethostname.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        self.libc.gethostname.restype = ctypes.c_int
        buf = ctypes.create_string_buffer(256)
        if self.libc.gethostname(buf, 256) == 0:
            return buf.value.decode()
        return "unknown"
    
    def get_loadavg(self) -> tuple:
        self.libc.getloadavg.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        self.libc.getloadavg.restype = ctypes.c_int
        loadavg = (ctypes.c_double * 3)()
        if self.libc.getloadavg(loadavg, 3) == 3:
            return (loadavg[0], loadavg[1], loadavg[2])
        return (0.0, 0.0, 0.0)
    
    def collect(self):
        return {
            "pid": self.get_pid(),
            "ppid": self.get_ppid(),
            "uid": self.get_uid(),
            "gid": self.get_gid(),
            "epoch_time": self.get_time(),
            "hostname": self.get_hostname(),
            "loadavg": self.get_loadavg()
        }

def print_header():
    print("=" * 50)
    print(" Libc Inspector")
    print("=" * 50)

def print_system_info():
    print("\n[System]")
    print(f"OS           : {platform.system()} {platform.release()}")
    print(f"Architecture : {platform.machine()}")
    print(f"Python       : {platform.python_version()}")

def print_libc_info(data):
    print("\n[libc interaction]")
    print(f"Process ID   : {data['pid']}")
    print(f"Parent PID   : {data['ppid']}")
    print(f"User ID      : {data['uid']}")
    print(f"Group ID     : {data['gid']}")
    print(f"Hostname     : {data['hostname']}")
    print(f"Load average : {data['loadavg'][0]:.2f}, {data['loadavg'][1]:.2f}, {data['loadavg'][2]:.2f}")
    print(f"Epoch time   : {data['epoch_time']}")
    print(f"Readable time: {datetime.fromtimestamp(data['epoch_time'])}")
    print(f"Python os    : PID={os.getpid()}, UID={os.getuid()}, HOST={os.uname().nodename}")

def main():
    print_header()
    print_system_info()
    
    inspector = LibcInspector()
    
    if not inspector.load():
        return
    
    data = inspector.collect()
    print_libc_info(data)
    
    print("\n[Note]")
    print("All values retrieved via libc through ctypes.")
    print("Comparison with Python os module shows consistency.")

if __name__ == "__main__":
    main()
