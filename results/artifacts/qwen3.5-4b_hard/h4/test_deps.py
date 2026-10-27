import pytest
from deps import resolve, CycleError
def test_basic(): assert resolve({"a":["b","c"],"b":["c"],"c":[]})==["c","b","a"]
def test_alpha_tiebreak(): assert resolve({"x":[],"a":[],"m":["x"]})==["a","x","m"]
def test_implicit_nodes(): assert resolve({"a":["z"]})==["z","a"]
def test_empty(): assert resolve({})==[]
def test_cycle():
    with pytest.raises(CycleError) as e: resolve({"a":["b"],"b":["c"],"c":["a"]})
    assert set(e.value.cycle)>={"a","b","c"}
def test_self(): 
    with pytest.raises(CycleError): resolve({"a":["a"]})
def test_diamond(): assert resolve({"d":["b","c"],"b":["a"],"c":["a"],"a":[]})==["a","b","c","d"]
