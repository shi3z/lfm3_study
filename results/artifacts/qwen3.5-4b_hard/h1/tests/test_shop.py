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
