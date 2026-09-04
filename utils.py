import datetime


def safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def iso_to_text(value):
    if not value:
        return None
    try:
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + " UTC"
        return text
    except Exception:
        return None


def nested_dict(value, *keys):
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def redact_secret(value, visible=0):
    if not value:
        return ""
    value = str(value)
    if visible <= 0:
        return "***"
    return value[:visible] + "***"
