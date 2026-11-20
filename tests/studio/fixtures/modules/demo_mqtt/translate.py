# Test connector: sends each state as "<id>/state" and takes no orders.
def subscriptions(options):
    return []


def outgoing(options, device, state):
    return [(f"{device['remote_id']}/state", (state or {}).get("state", ""))]


def incoming(options, devices, topic, payload):
    return None
