def normalize_error(err):
    if isinstance(err, dict):
        return err
    return {
        "action": "unknown",
        "message": str(err),
        "recoverable": True
    }
