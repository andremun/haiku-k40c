#!/usr/bin/env python3
"""Talk to the QEMU human monitor of the test VM.

  qemu_hmp.py SOCKET cmd  'screendump /tmp/s.ppm'   one monitor command
  qemu_hmp.py SOCKET type 'uname -a'                type a line + Return
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
import socket
import sys
import time

PLAIN = {' ': 'spc', '-': 'minus', '=': 'equal', '.': 'dot', ',': 'comma', '/': 'slash',
         ';': 'semicolon', "'": 'apostrophe', '[': 'bracket_left', ']': 'bracket_right',
         '\\': 'backslash', '`': 'grave_accent'}
SHIFT = {'_': 'minus', '+': 'equal', '>': 'dot', '<': 'comma', '?': 'slash', ':': 'semicolon',
         '"': 'apostrophe', '{': 'bracket_left', '}': 'bracket_right', '|': 'backslash',
         '~': 'grave_accent', '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6',
         '&': '7', '*': '8', '(': '9', ')': '0'}


def key(c):
    if c.islower() or c.isdigit():
        return c
    if c.isupper():
        return 'shift-' + c.lower()
    if c in PLAIN:
        return PLAIN[c]
    if c in SHIFT:
        return 'shift-' + SHIFT[c]
    raise SystemExit(f"no key for {c!r}")


def main():
    path, mode, text = sys.argv[1], sys.argv[2], sys.argv[3]
    s = socket.socket(socket.AF_UNIX)
    s.connect(path)
    time.sleep(0.2)
    s.recv(65536)
    if mode == "cmd":
        s.sendall((text + "\n").encode())
        time.sleep(0.8)
        print(s.recv(65536).decode(errors="replace"))
        return
    for c in text:
        s.sendall(f"sendkey {key(c)} 20\n".encode())
        time.sleep(0.07)
        s.recv(65536)
    s.sendall(b"sendkey ret\n")
    time.sleep(0.5)


main()
