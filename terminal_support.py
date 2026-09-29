"""지원하는 터미널에서 ANSI 색상을 활성화합니다."""

import os
import sys


def enable_color():
    if not sys.stdout.isatty() or "NO_COLOR" in os.environ or os.environ.get("TERM") == "dumb":
        return False
    if os.name != "nt":
        return True
    try:
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetStdHandle.argtypes = [wintypes.DWORD]
        kernel.GetStdHandle.restype = wintypes.HANDLE
        kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        handle = kernel.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = wintypes.DWORD()
        if not kernel.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING. 다른 콘솔 모드 비트는 유지합니다.
        return bool(kernel.SetConsoleMode(handle, mode.value | 0x0004))
    except (AttributeError, OSError):
        return False


def clear_screen():
    """대화형 터미널 화면만 비워 다음 화면을 맨 위에 표시합니다."""
    if not sys.stdout.isatty():
        return False
    if os.name != "nt" and os.environ.get("TERM") in (None, "", "dumb"):
        return False
    command = "cls" if os.name == "nt" else "clear"
    return os.system(command) == 0
