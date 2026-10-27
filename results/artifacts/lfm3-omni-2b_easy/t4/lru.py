class LRUCache:
    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.cache = {}
        self.head = {}
        self.tail = {}

    def get(self, key: str) -> str | None:
        if key in self.cache:
            self.cache[key] = self.cache.pop(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: str) -> None:
        if key in self.cache:
            self.cache[key] = value
        else:
            if len(self.cache) >= self.capacity:
                # Evict least recently used item
                lru, lru_key = self.tail.pop()
                del self.cache[lru_key]
            self.cache[key] = value
            self.head[key] = self.head
            self.tail[key] = self.tail
            self.size += 1

    def remove(self, key: str) -> None:
        if key in self.cache:
            del self.cache[key]
            self.head[key] = None
            self.tail[key] = None

    def size(self) -> int:
        return len(self.cache)

    def get_most_recent(self) -> str | None:
        if self.size() == 0:
            return None
        return next((key for key in self.head if key is not None), None)
