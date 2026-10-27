from app.core.settings import get_request_budget, get_retries
from app.utils.h1 import helper_1
def handle(req):
    deadline = get_request_budget()
    return helper_1(deadline)
