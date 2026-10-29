# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Role-fixed signing for one reviewed physical launch. Never called in rehearsal."""
import os
from pathlib import Path
import stat

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tools.memstage import build


def load(role, suite):
    if role not in ("A7", "memory") or os.geteuid() == 0:
        raise ValueError("signing role/root denied")
    folder = build.PACKAGE / "a7" if role == "A7" else build.PACKAGE
    expected = (
        suite["A7"]["public_key_hex"] if role == "A7" else suite["public_key_hex"]
    )
    fd = os.open(folder / "host-key.pem", os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise ValueError("signing input permissions")
        data = stream.read(4097)
    if len(data) > 4096:
        raise ValueError("signing input bound")
    key = serialization.load_pem_private_key(data, password=None)
    if (
        not isinstance(key, Ed25519PrivateKey)
        or key.public_key()
        .public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        .hex()
        != expected
    ):
        raise ValueError("signing key differs from reviewed package")
    return key


def grant(role, request, digest, suite):
    if len(digest) != 32 or not any(digest):
        raise ValueError("fresh proof digest missing")
    message = bytearray(request)
    if role == "A7":
        if len(message) != 128 or message[:16] != b"K40A7REQ\x01" + bytes(7):
            raise ValueError("A7 request role")
        message[:8] = b"K40A7ARM"
        message[72:80] = request[56:64]
        message[80:112] = digest
    elif role == "memory":
        if len(message) != 256 or message[:16] != b"K40MEMREQ\x01" + bytes(6):
            raise ValueError("memory request role")
        message[:16] = b"K40MEMRUN\x01" + bytes(6)
        message[192:224] = digest
    else:
        raise ValueError("unknown signing role")
    return bytes(message) + load(role, suite).sign(bytes(message))
