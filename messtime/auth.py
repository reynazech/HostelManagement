"""Admin password storage. Only a salted PBKDF2 hash is kept in the database."""

import hashlib
import hmac
import secrets
import sqlite3

from . import db

_SETTING = "admin_password"
_ITERATIONS = 200_000


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)


def has_password(conn: sqlite3.Connection) -> bool:
    return db.get_setting(conn, _SETTING) is not None


def set_password(conn: sqlite3.Connection, password: str) -> None:
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    salt = secrets.token_bytes(16)
    db.set_setting(conn, _SETTING, f"{salt.hex()}:{_hash(password, salt).hex()}")


def check_password(conn: sqlite3.Connection, password: str) -> bool:
    stored = db.get_setting(conn, _SETTING)
    if stored is None:
        return False
    salt_hex, hash_hex = stored.split(":")
    return hmac.compare_digest(_hash(password, bytes.fromhex(salt_hex)).hex(), hash_hex)
