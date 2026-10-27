import pytest
from expr import evaluate
@pytest.mark.parametrize("s,v",[("1+2*3",7),("(1+2)*3",9),("2^3^2",512),("-3+5",2),("--3",3),("2*-3",-6),("10/4",2.5),("1 - 2 - 3",-4),("2*(3+(4-1))",12),("  7 ",7),("1.5+2.5",4),("-(2+3)",-5),("2^-1",0.5),("8/2/2",2)])
def test_ok(s,v): assert evaluate(s)==pytest.approx(v)
@pytest.mark.parametrize("s",["","1+","(1+2","1+2)","*3","1 2","a+1","1/0"])
def test_err(s):
    with pytest.raises(ValueError): evaluate(s)
