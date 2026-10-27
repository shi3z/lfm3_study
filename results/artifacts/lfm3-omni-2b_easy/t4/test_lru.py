from lru import LRUCache

def test_lru_cache():
    cache = LRUCache(capacity=3)

    # Test 1: get existing key
    cache.put("key1", "value1")
    assert cache.get("key1") == "value1", "Test 1 failed: get key1"

    # Test 2: get non-existent key returns None
    assert cache.get("nonexistent") is None, "Test 2 failed: get non-existent"

    # Test 3: put new key, size should be 1
    cache.put("key2", "value2")
    assert cache.size() == 1, "Test 3 failed: size should be 1"

    # Test 4: put another key, size should be 2
    cache.put("key3", "value3")
    assert cache.size() == 2, "Test 4 failed: size should be 2"

    # Test 5: evict least recently used (LRU)
    cache.put("key4", "value4")
    assert cache.size() == 3, "Test 5 failed: size should be 3"
    assert cache.get_most_recent() == "key4", "Test 5 failed: most recent should be key4"

    # Test 6: evict key2 (least recently used)
    cache.remove("key2")
    assert cache.size() == 2, "Test 6 failed: size should be 2 after removing key2"
    assert cache.get_most_recent() == "key3", "Test 6 failed: most recent should be key3"

    # Test 7: evict key1 (least recently used)
    cache.remove("key1")
    assert cache.size() == 1, "Test 7 failed: size should be 1 after removing key1"
    assert cache.get_most_recent() == "key3", "Test 7 failed: most recent should be key3"

    # Test 8: put new key, size should be 2
    cache.put("key5", "value5")
    assert cache.size() == 2, "Test 8 failed: size should be 2 after putting key5"
    assert cache.get_most_recent() == "key5", "Test 8 failed: most recent should be key5"

    print("All tests passed!")

if __name__ == "__main__":
    test_lru_cache()
