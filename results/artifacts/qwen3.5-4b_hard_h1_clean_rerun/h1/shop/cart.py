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
