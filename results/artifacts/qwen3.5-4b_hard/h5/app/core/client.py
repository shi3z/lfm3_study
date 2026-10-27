from app.core.settings import get_retries
def fetch(url):
    for _ in range(get_retries()): pass
