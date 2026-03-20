#!/usr/bin/env python3

import ctypes
import os
import platform
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


class LibcInspector:
    def __init__(self) -> None:
        self.libc = None
        self.system = platform.system()

    def load(self) -> bool:
        libc_names = {
            "Linux": "libc.so.6",
            "Darwin": "libc.dylib",
            "Windows": "msvcrt.dll",
        }

        libc_name = libc_names.get(self.system)
        if libc_name is None:
            print(f"[ERROR] Unsupported platform: {self.system}")
            return False

        try:
            self.libc = ctypes.CDLL(libc_name)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load libc '{libc_name}': {e}")
            return False

    def _has_function(self, name: str) -> bool:
        return self.libc is not None and hasattr(self.libc, name)

    def get_pid(self) -> Optional[int]:
        if not self._has_function("getpid"):
            return None
        self.libc.getpid.argtypes = []
        self.libc.getpid.restype = ctypes.c_int
        return self.libc.getpid()

    def get_ppid(self) -> Optional[int]:
        if not self._has_function("getppid"):
            return None
        self.libc.getppid.argtypes = []
        self.libc.getppid.restype = ctypes.c_int
        return self.libc.getppid()

    def get_time(self) -> Optional[int]:
        if not self._has_function("time"):
            return None
        self.libc.time.argtypes = [ctypes.c_void_p]
        self.libc.time.restype = ctypes.c_long
        return int(self.libc.time(None))

    def get_uid(self) -> Optional[int]:
        if not self._has_function("getuid"):
            return None
        self.libc.getuid.argtypes = []
        self.libc.getuid.restype = ctypes.c_uint
        return self.libc.getuid()

    def get_gid(self) -> Optional[int]:
        if not self._has_function("getgid"):
            return None
        self.libc.getgid.argtypes = []
        self.libc.getgid.restype = ctypes.c_uint
        return self.libc.getgid()

    def get_hostname(self) -> Optional[str]:
        if not self._has_function("gethostname"):
            return None
        self.libc.gethostname.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        self.libc.gethostname.restype = ctypes.c_int
        buf = ctypes.create_string_buffer(256)
        if self.libc.gethostname(buf, len(buf)) == 0:
            return buf.value.decode(errors="ignore")
        return None

    def get_loadavg(self) -> Optional[Tuple[float, float, float]]:
        if not self._has_function("getloadavg"):
            return None
        self.libc.getloadavg.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        self.libc.getloadavg.restype = ctypes.c_int
        loadavg = (ctypes.c_double * 3)()
        result = self.libc.getloadavg(loadavg, 3)
        if result == 3:
            return (loadavg[0], loadavg[1], loadavg[2])
        return None

    def collect(self) -> Dict[str, Any]:
        return {
            "pid": self.get_pid(),
            "ppid": self.get_ppid(),
            "uid": self.get_uid(),
            "gid": self.get_gid(),
            "epoch_time": self.get_time(),
            "hostname": self.get_hostname(),
            "loadavg": self.get_loadavg(),
        }


def format_value(value: Any) -> str:
    if value is None:
        return "N/A"
    return str(value)


def print_header() -> None:
    print("=" * 56)
    print(" Libc Inspector")
    print("=" * 56)


def print_system_info() -> None:
    print("\n[System]")
    print(f"OS           : {platform.system()} {platform.release()}")
    print(f"Architecture : {platform.machine()}")
    print(f"Python       : {platform.python_version()}")


def print_libc_info(data: Dict[str, Any]) -> None:
    print("\n[libc interaction]")
    print(f"Process ID   : {format_value(data['pid'])}")
    print(f"Parent PID   : {format_value(data['ppid'])}")
    print(f"User ID      : {format_value(data['uid'])}")
    print(f"Group ID     : {format_value(data['gid'])}")
    print(f"Hostname     : {format_value(data['hostname'])}")

    loadavg = data["loadavg"]
    if loadavg is None:
        print("Load average : N/A")
    else:
        print(f"Load average : {loadavg[0]:.2f}, {loadavg[1]:.2f}, {loadavg[2]:.2f}")

    epoch_time = data["epoch_time"]
    print(f"Epoch time   : {format_value(epoch_time)}")
    if epoch_time is None:
        print("Readable time: N/A")
    else:
        print(f"Readable time: {datetime.fromtimestamp(epoch_time)}")


def print_python_comparison() -> None:
    print("\n[Python os module comparison]")

    pid = getattr(os, "getpid", lambda: None)()
    print(f"Process ID   : {format_value(pid)}")

    ppid = getattr(os, "getppid", lambda: None)()
    print(f"Parent PID   : {format_value(ppid)}")

    uid_func = getattr(os, "getuid", None)
    uid = uid_func() if callable(uid_func) else None
    print(f"User ID      : {format_value(uid)}")

    gid_func = getattr(os, "getgid", None)
    gid = gid_func() if callable(gid_func) else None
    print(f"Group ID     : {format_value(gid)}")

    uname_func = getattr(os, "uname", None)
    hostname = uname_func().nodename if callable(uname_func) else platform.node()
    print(f"Hostname     : {format_value(hostname)}")


def print_note() -> None:
    print("\n[Note]")
    print("Values above were retrieved via libc through ctypes when available.")
    print("The Python os module section provides a simple consistency check.")


def main() -> None:
    print_header()
    print_system_info()

    inspector = LibcInspector()
    if not inspector.load():
        return

    data = inspector.collect()
    print_libc_info(data)
    print_python_comparison()
    print_note()


if __name__ == "__main__":
    main()
