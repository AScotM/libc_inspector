#!/usr/bin/env python3

import ctypes
import platform
import os
from datetime import datetime


class LibcInspector:
    def __init__(self):
        self.libc = None

    def load(self):
        try:
            self.libc = ctypes.CDLL("libc.so.6")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load libc: {e}")
            return False

    def get_pid(self) -> int:
        self.libc.getpid.restype = ctypes.c_int
        return self.libc.getpid()

    def get_time(self) -> int:
        self.libc.time.restype = ctypes.c_long
        return self.libc.time(None)

    def get_uid(self) -> int:
        self.libc.getuid.restype = ctypes.c_uint
        return self.libc.getuid()

    def collect(self):
        return {
            "pid": self.get_pid(),
            "uid": self.get_uid(),
            "epoch_time": self.get_time(),
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
    print(f"User ID      : {data['uid']}")
    print(f"Epoch time   : {data['epoch_time']}")
    print(f"Readable time: {datetime.fromtimestamp(data['epoch_time'])}")


def main():
    print_header()
    print_system_info()

    inspector = LibcInspector()

    if not inspector.load():
        return

    data = inspector.collect()
    print_libc_info(data)

    print("\n[Note]")
    print("All values retrieved via glibc through ctypes.")


if __name__ == "__main__":
    main()
