def test_basic():
    from parse import parse_kv
    assert parse_kv("a=1,b=2") == {"a": 1, "b": 2}

def test_spaces():
    assert parse_kv(" a = 1 , b=2 ") == {"a": 1, "b": 2}

def test_empty():
    assert parse_kv("") == {}

def test_trailing():
    assert parse_kv("a=1,") == {"a": 1}
