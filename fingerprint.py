import os
import json
from config import FINGERPRINT_FILE


def _load_fingerprints():
    if not os.path.exists(FINGERPRINT_FILE):
        return set()
    try:
        with open(FINGERPRINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
            return set()
    except Exception:
        return set()


def _save_fingerprints(s: set):
    try:
        with open(FINGERPRINT_FILE, "w", encoding="utf-8") as f:
            json.dump(list(s), f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def fingerprint_exists(fp: str) -> bool:
    """Return True if fingerprint already exists on disk."""
    s = _load_fingerprints()
    return fp in s


def add_fingerprint(fp: str):
    """Add a fingerprint to the persistent store (idempotent)."""
    s = _load_fingerprints()
    if fp in s:
        return
    s.add(fp)
    _save_fingerprints(s)
