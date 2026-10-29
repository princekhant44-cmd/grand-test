"""Interest rules the model file cannot express: who may set the status."""

PENDING = "pending"


def _start_pending(payload):
    """A new interest always starts pending; only the receiver can accept or decline it."""
    data = payload.get("data")
    if isinstance(data, dict):
        data["status"] = PENDING
    return payload


def _receiver_changes_status_only(payload):
    """The receiver may answer an interest, not edit who sent it or what it said."""
    data = payload.get("data")
    if isinstance(data, dict):
        payload["data"] = {key: value for key, value in data.items() if key == "status"}
    return payload


def register(kirak):
    kirak.on("interests").hook("before_create")(_start_pending)
    kirak.on("interests").hook("before_update")(_receiver_changes_status_only)
