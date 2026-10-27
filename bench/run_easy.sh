#!/bin/bash
# each task: fresh dir, run claude -p against LFM3, objective check
export ANTHROPIC_BASE_URL=${BASE_URL:-http://127.0.0.1:8321} ANTHROPIC_API_KEY=dummy ANTHROPIC_MODEL=lfm3 ANTHROPIC_SMALL_FAST_MODEL=lfm3 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
B=${BENCH_ROOT:-$(cd "$(dirname "$0")" && pwd)}; R=${OUT:-$B/runs_easy}; rm -rf $R; mkdir -p $R
PY=${PY:-python3}
run() { # name prompt check_cmd
  d=$R/$1; mkdir -p $d; cd $d; eval "setup_$1"
  s=$(date +%s)
  timeout 400 claude -p "$2" --dangerously-skip-permissions --max-turns 15 > out.txt 2>&1
  e=$(( $(date +%s)-s ))
  if (eval "$3") >check.txt 2>&1; then r=PASS; else r=FAIL; fi
  echo "$1 $r ${e}s"
}
setup_t1() { cat > stack.py <<'P'
class Stack:
    def __init__(self): self.items=[]
    def push(self,x): self.items.append(x)
    def pop(self): return self.items.pop(0)
    def peek(self): return self.items[0]
P
cat > test_stack.py <<'P'
from stack import Stack
def test_lifo():
    s=Stack(); s.push(1); s.push(2); assert s.pop()==2 and s.peek()==1
P
}
setup_t2() { :; }
setup_t3() { mkdir -p pkg; echo 'def calc_total(xs): return sum(xs)' > pkg/util.py
 echo 'from pkg.util import calc_total
print(calc_total([1,2,3]))' > main.py
 echo 'from pkg.util import calc_total
def f(): return calc_total([4])' > other.py; }
setup_t4() { cat > lru.py <<'P'
class LRUCache:
    """TODO: implement LRU cache with get(key)->value or -1 and put(key,value). capacity in __init__."""
P
cat > test_lru.py <<'P'
from lru import LRUCache
def test_lru():
    c=LRUCache(2); c.put(1,1); c.put(2,2); assert c.get(1)==1
    c.put(3,3); assert c.get(2)==-1
    c.put(4,4); assert c.get(1)==-1 and c.get(3)==3 and c.get(4)==4
    c.put(3,30); assert c.get(3)==30
P
}
setup_t5() { cat > parse.py <<'P'
def parse_kv(s):
    out={}
    for part in s.split(','):
        k,v=part.split('=')
        out[k]=int(v)
    return out
P
cat > test_parse.py <<'P'
from parse import parse_kv
def test_basic(): assert parse_kv("a=1,b=2")=={"a":1,"b":2}
def test_spaces(): assert parse_kv(" a = 1 , b=2 ")=={"a":1,"b":2}
def test_empty(): assert parse_kv("")=={}
def test_trailing(): assert parse_kv("a=1,")=={"a":1}
P
}
run t1 "test_stack.py のテストが落ちる。pytest を実行して原因を調べ、stack.py を修正して。" "$PY -m pytest -q test_stack.py"
run t2 "hello.py を作成し、フィボナッチ数列の n 番目を返す関数 fib(n) を実装して。fib(10)==55。ファイルを実行して確認もして。" "$PY -c 'from hello import fib; assert fib(10)==55 and fib(0)==0 and fib(1)==1'"
run t3 "pkg/util.py の関数 calc_total を compute_sum にリネームし、使用箇所を全て更新して。" "! grep -rq calc_total . --include=*.py && grep -q compute_sum pkg/util.py && $PY main.py | grep -q 6 && $PY -c 'from other import f; assert f()==4'"
run t4 "lru.py に LRUCache を実装して test_lru.py を通して。" "$PY -m pytest -q test_lru.py"
run t5 "parse.py の parse_kv を、test_parse.py の全テストが通るように修正して。pytest で確認して。" "$PY -m pytest -q test_parse.py"
