#!/usr/bin/env python3
"""Portable path resolution for the ledger kit.

Nothing in this package assumes a drive letter, a user name, an OS, or a Python
version directory. A config file may use these forms for any path field:

    @here/data          -> <directory containing the config file>/data
    @pkg/data           -> <directory containing this package>/data (= parent of the package's gateway/ dir)
    ~/data              -> <current user's home>/data   (also @home)
    data                -> <directory containing the config file>/data  (relative)
    /absolute/path      -> used as-is (also a drive-letter path on Windows)

Stdlib only; works on Windows, Linux and macOS.
"""
from __future__ import annotations

import json
import os

PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_FIELDS = ("out_dir", "web_root", "collector_script", "log_dir", "active_log")


def expand_path(value, config_dir=None):
    """Turn one path value from config into a portable absolute path."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return ""
    base = config_dir or PKG_DIR
    if s.startswith("@here"):
        rest = s[len("@here"):].lstrip("/\\")
        s = os.path.join(base, rest) if rest else base
    elif s.startswith("@pkg"):
        rest = s[len("@pkg"):].lstrip("/\\")
        s = os.path.join(PKG_DIR, rest) if rest else PKG_DIR
    elif s.startswith("@home"):
        rest = s[len("@home"):].lstrip("/\\")
        s = os.path.join(os.path.expanduser("~"), rest) if rest else os.path.expanduser("~")
    elif s == "~" or s.startswith("~/") or s.startswith("~\\"):
        s = os.path.expanduser(s)
    # Plain relative paths must resolve against the CONFIG FILE's directory,
    # not the process CWD. @here / @pkg / @home / ~ already produced an
    # absolute path above, so this branch only affects bare "data"-style values.
    if not os.path.isabs(s) and not os.path.splitdrive(s)[0]:
        s = os.path.join(base, s)
    return os.path.normpath(os.path.abspath(s))


def load_config(path):
    """Read a JSON config and normalise every path field in place.

    Adds two bookkeeping keys (config_path, config_dir); they are inert for the
    ledger, the daily report and the HTML report.
    """
    config_path = os.path.abspath(os.path.expanduser(str(path)))
    config_dir = os.path.dirname(config_path)
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    for key in PATH_FIELDS:
        if key in cfg and cfg[key] not in (None, ""):
            cfg[key] = expand_path(cfg[key], config_dir)
    cfg["config_path"] = config_path
    cfg["config_dir"] = config_dir
    return cfg


def ports_from_config(path, default_port=8080, default_lock_port=43176):
    """Read (team listen port, watchdog lock port) from a config file.

    ``listen`` may be ``host:port`` or ``[::]:port``; ``rpartition(":")``
    yields the trailing port in both forms. A missing, unreadable, or
    malformed config falls back to the supplied defaults, so a bad file can
    never prevent the watchdog from starting. Stdlib only, all platforms.
    """
    port, lock_port = default_port, default_lock_port
    try:
        with open(os.path.abspath(os.path.expanduser(str(path))), encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError, TypeError, AttributeError):
        return port, lock_port
    if not isinstance(cfg, dict):
        return port, lock_port
    listen = str(cfg.get("listen") or "")
    if ":" in listen:
        try:
            port = int(listen.rpartition(":")[2])
        except (ValueError, TypeError, AttributeError):
            pass
    try:
        raw = cfg.get("watchdog_lock_port")
        if raw not in (None, ""):
            lock_port = int(raw)
    except (ValueError, TypeError, AttributeError):
        pass
    return port, lock_port


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        import pprint
        pprint.pprint(load_config(sys.argv[1]))
