#!/bin/bash
export ANTHROPIC_BASE_URL=${BASE_URL:-http://127.0.0.1:8321} ANTHROPIC_API_KEY=dummy ANTHROPIC_MODEL=lfm3 ANTHROPIC_SMALL_FAST_MODEL=lfm3 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
B=${BENCH_ROOT:-$(cd "$(dirname "$0")" && pwd)}; R=${OUT:-$B/runs_hard}; H=$B/hidden; PY=${PY:-python3}; [ -z "$ONLY" ] && rm -rf $R; mkdir -p $R
run() { [ -n "$ONLY" ] && [ "$ONLY" != "$1" ] && return; d=$R/$1; mkdir -p $d; cd $d; eval "setup_$1"
  s=$(date +%s); timeout 900 claude -p "$2" --dangerously-skip-permissions --max-turns 40 > out.txt 2>&1 </dev/null
  e=$(( $(date +%s)-s )); if (eval "$3") >check.txt 2>&1; then r=PASS; else r=FAIL; fi; echo "$1 $r ${e}s"; }
setup_h1() { mkdir -p shop tests
cat > shop/__init__.py <<'P'
P
cat > shop/pricing.py <<'P'
def apply_discount(price, pct):
    """Return price after pct percent discount, rounded to 2 decimals."""
    return round(price * (1 - pct / 10), 2)

def add_tax(price, rate=0.08):
    return round(price * (1 + rate), 2)
P
cat > shop/inventory.py <<'P'
class OutOfStock(Exception): pass
class Inventory:
    def __init__(self, stock=None):
        self.stock = dict(stock or {})
    def reserve(self, sku, qty):
        if self.stock.get(sku, 0) < qty - 1:
            raise OutOfStock(sku)
        self.stock[sku] = self.stock.get(sku, 0) - qty
    def release(self, sku, qty):
        self.stock[sku] = self.stock.get(sku, 0) + qty
P
cat > shop/cart.py <<'P'
from .pricing import apply_discount, add_tax
class Cart:
    def __init__(self, inventory, items={}):
        self.inventory = inventory
        self.items = items   # sku -> (unit_price, qty)
    def add(self, sku, unit_price, qty=1):
        self.inventory.reserve(sku, qty)
        p, q = self.items.get(sku, (unit_price, 0))
        self.items[sku] = (p, q + qty)
    def remove(self, sku, qty=1):
        p, q = self.items[sku]
        q -= qty
        self.items[sku] = (p, q)
        self.inventory.release(sku, qty)
    def total(self, discount_pct=0):
        sub = sum(p * q for p, q in self.items.values())
        return add_tax(apply_discount(sub, discount_pct))
P
cat > tests/test_shop.py <<'P'
import pytest
from shop.cart import Cart
from shop.inventory import Inventory, OutOfStock
from shop.pricing import apply_discount, add_tax
def test_discount(): assert apply_discount(200, 10) == 180.0
def test_tax(): assert add_tax(100) == 108.0
def test_reserve_exact():
    inv = Inventory({"a": 2}); inv.reserve("a", 2); assert inv.stock["a"] == 0
def test_reserve_over():
    inv = Inventory({"a": 2})
    with pytest.raises(OutOfStock): inv.reserve("a", 3)
def test_carts_independent():
    inv = Inventory({"a": 9}); c1 = Cart(inv); c2 = Cart(inv)
    c1.add("a", 10); assert c2.items == {}
def test_remove_to_zero():
    inv = Inventory({"a": 5}); c = Cart(inv); c.add("a", 10, 2); c.remove("a", 2)
    assert "a" not in c.items and inv.stock["a"] == 5
def test_total():
    inv = Inventory({"a": 9}); c = Cart(inv); c.add("a", 50, 2)
    assert c.total(discount_pct=10) == 97.2
P
cp tests/test_shop.py /tmp/h1_orig.py; }
setup_h2() { printf 'def evaluate(s: str) -> float:\n    """Evaluate arithmetic: + - * / ^ (right-assoc, binds tighter than unary minus on its left operand? no: standard: 2^-1=0.5), parentheses, unary minus, floats.\n    Raise ValueError on any malformed input or division by zero."""\n    raise NotImplementedError\n' > expr.py; }
setup_h3() { cat > wordfreq.py <<'P'
import re, sys
from collections import Counter

def top_words(text, n=10):
    words = re.findall(r"[a-z']+", text.lower())
    return Counter(words).most_common(n)

def main(argv):
    text = open(argv[1]).read()
    for w, c in top_words(text):
        print(f"{w}\t{c}")

if __name__ == "__main__":
    main(sys.argv)
P
}
setup_h4() { printf 'class CycleError(Exception):\n    def __init__(self, cycle):\n        super().__init__(f"cycle: {cycle}")\n        self.cycle = cycle\n\ndef resolve(graph):\n    raise NotImplementedError\n' > deps.py; }
setup_h5() { mkdir -p app/core app/api app/utils tests
for i in 1 2 3 4 5 6; do echo "def helper_$i(x): return x+$i" > app/utils/h$i.py; done
cat > app/core/settings.py <<'P'
import os
DEFAULT_RETRIES = 3
def get_retries():
    return int(os.environ.get("APP_RETRIES", DEFAULT_RETRIES))
def get_request_budget():
    """Seconds allowed per request; env APP_BUDGET_S, default 12.5."""
    return float(os.environ.get("APP_BUDGET_S", "12.5"))
P
cat > app/core/client.py <<'P'
from app.core.settings import get_retries
def fetch(url):
    for _ in range(get_retries()): pass
P
cat > app/api/handlers.py <<'P'
from app.core.settings import get_request_budget, get_retries
from app.utils.h1 import helper_1
def handle(req):
    deadline = get_request_budget()
    return helper_1(deadline)
P
cat > app/api/health.py <<'P'
from app.core.settings import get_request_budget
def ping(): return get_request_budget() > 0
P
cat > app/utils/log.py <<'P'
import os
LEVEL = os.environ.get("APP_LOG", "info")
P
echo "from app.api.handlers import handle" > app/main.py; }
run h1 "tests/test_shop.py のテストが複数失敗している。pytest を実行して原因を調べ、shop/ パッケージのバグを全て直して。テストは変更しないこと。" "cmp tests/test_shop.py /tmp/h1_orig.py && $PY -m pytest -q tests"
run h2 "expr.py の evaluate を実装して。+ - * / ^(右結合、2^3^2=512、2^-1=0.5)、括弧、単項マイナス、小数に対応。不正な式(空、括弧の不一致、演算子の欠落、未知の文字、ゼロ除算)は ValueError。自分でテストを書いて pytest で確認すること。" "cp $H/test_expr.py . && $PY -m pytest -q test_expr.py"
run h3 "wordfreq.py を拡張して。(1) top_words(text, n=10, stopwords=None, min_length=1): stopwords(set)の語を除外、min_length未満の語を除外、同数は単語のアルファベット順。(2) CLI: python wordfreq.py FILE [--top N] [--stopwords a,b,c] [--min-length K] [--json]。--json のときは [[word,count],...] を JSON で標準出力。指定なしは従来どおり 'word<TAB>count'。" "cp $H/test_wf.py . && $PY -m pytest -q test_wf.py"
run h4 "deps.py の resolve(graph) を実装して。graph は {ノード: [依存先...]}。依存先が先に来るトポロジカル順のリストを返す。依存先のみで定義されていないノードも結果に含める。選択肢が複数ある場合はアルファベット順で最小を先に。循環があれば CycleError(cycle=循環に含まれるノードのリスト) を送出(自己ループも)。テストを自分で書いて確認すること。" "cp $H/test_deps.py . && $PY -m pytest -q test_deps.py"
run h5 "このリポジトリで、リクエストの制限時間(秒)を決めている環境変数名とそのデフォルト値、それを読む関数名、その関数を呼んでいるモジュールのファイルパスを全て調べ、結果を ANSWER.txt に書いて。" "grep -q APP_BUDGET_S ANSWER.txt && grep -q 12.5 ANSWER.txt && grep -q get_request_budget ANSWER.txt && grep -q handlers.py ANSWER.txt && grep -q health.py ANSWER.txt && ! grep -q client.py ANSWER.txt"
