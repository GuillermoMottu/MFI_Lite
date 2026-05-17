import state as app_state


def is_cloud_connected() -> bool:
    return app_state.state["cloud_connected"]


def set_cloud_connected(value: bool) -> None:
    app_state.state["cloud_connected"] = value


def increment_buffer_pending(n: int = 1) -> None:
    app_state.state["buffer_pending"] += n


def decrement_buffer_pending(n: int = 1) -> None:
    app_state.state["buffer_pending"] = max(0, app_state.state["buffer_pending"] - n)
