import json
import os
import tempfile


def safe_str(value, default=""):
    if value is None:
        return default
    try:
        return str(value)
    except Exception:
        return default


def safe_float(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=None):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clamp(value, low, high):
    return max(low, min(high, value))


def format_number(value, decimals=1, default="N/A"):
    if value is None:
        return default
    try:
        return ("{:.%df}" % decimals).format(float(value))
    except (TypeError, ValueError):
        return default


def format_coordinate(value):
    number = safe_float(value)
    return "N/A" if number is None else "{:.6f}".format(number)


def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data
    except (OSError, ValueError, TypeError):
        return default


def save_json_atomic(path, data):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".myskoda-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
