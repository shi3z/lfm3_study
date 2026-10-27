from app.core.settings import get_request_budget
def ping(): return get_request_budget() > 0
