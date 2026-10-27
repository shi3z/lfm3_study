import os
DEFAULT_RETRIES = 3
def get_retries():
    return int(os.environ.get("APP_RETRIES", DEFAULT_RETRIES))
def get_request_budget():
    """Seconds allowed per request; env APP_BUDGET_S, default 12.5."""
    return float(os.environ.get("APP_BUDGET_S", "12.5"))
