"""지원하는 터미널에서 ANSI 색상을 활성화합니다."""

import os
import sys
import unicodedata


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


class InputCancelled(Exception):
    """대화형 필드에서 Esc를 눌러 현재 작업을 취소했습니다."""


def _character_width(character):
    if unicodedata.combining(character):
        return 0
    return 2 if unicodedata.east_asian_width(character) in ("W", "F") else 1


def _erase_last_character(characters):
    if not characters:
        return
    character = characters.pop()
    width = _character_width(character)
    if width == 0 and characters:
        width = _character_width(characters.pop())
    sys.stdout.write("\b \b" * width)
    sys.stdout.flush()


def _read_windows_line(prompt):
    import msvcrt

    sys.stdout.write(prompt)
    sys.stdout.flush()
    characters = []
    pending_character = None
    while True:
        character = pending_character if pending_character is not None else msvcrt.getwch()
        pending_character = None
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDBFF:
            following = msvcrt.getwch()
            if 0xDC00 <= ord(following) <= 0xDFFF:
                codepoint = 0x10000 + ((codepoint - 0xD800) << 10) + ord(following) - 0xDC00
                character = chr(codepoint)
            else:
                pending_character = following
                continue
        if character in ("\x00", "\xe0"):
            msvcrt.getwch()  # 방향키 같은 확장 키 입력을 무시합니다.
            continue
        if character == "\x1b":
            sys.stdout.write("\n")
            sys.stdout.flush()
            raise InputCancelled
        if character in ("\r", "\n"):
            sys.stdout.write("\n")
            sys.stdout.flush()
            return "".join(characters)
        if character == "\x03":
            raise KeyboardInterrupt
        if character in ("\b", "\x7f"):
            _erase_last_character(characters)
            continue
        if character.isprintable():
            characters.append(character)
            sys.stdout.write(character)
            sys.stdout.flush()


def _read_posix_line(prompt):
    import termios
    import tty

    descriptor = sys.stdin.fileno()
    previous = termios.tcgetattr(descriptor)
    characters = []
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        tty.setraw(descriptor)
        while True:
            character = sys.stdin.read(1)
            if character == "\x1b":
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                raise InputCancelled
            if character in ("\r", "\n"):
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                return "".join(characters)
            if character == "\x03":
                raise KeyboardInterrupt
            if character in ("\b", "\x7f"):
                _erase_last_character(characters)
                continue
            if character.isprintable():
                characters.append(character)
                sys.stdout.write(character)
                sys.stdout.flush()
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)


def read_console_line(prompt, cancel_on_escape=False):
    """필요하면 TTY 키 입력을 직접 읽어 Enter 없이 Esc 취소를 허용합니다."""
    if not cancel_on_escape:
        return input(prompt)
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        value = input(prompt)
        if value == "\x1b":
            raise InputCancelled
        return value
    if os.name == "nt":
        return _read_windows_line(prompt)
    return _read_posix_line(prompt)
