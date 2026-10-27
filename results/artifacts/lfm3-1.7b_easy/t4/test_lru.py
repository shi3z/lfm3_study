import sys
sys.path.insert(0, '<ROOT>/runs_easy/t4')
from lru import LRUCache


def test_lru():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    c.put(3, 3)
    assert c.get(2) == -1
    c.put(4, 4)
    assert c.get(1) == -1 and c.get(3) == 3 and c.get(4) == 4
    c.put(3, 30)
    assert c.get(3) == 30

if __name__ == "__main__":
    test_lru()
    print("All tests passed")
