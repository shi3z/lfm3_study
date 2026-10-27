from shop.pricing import apply_discount, add_tax


class Cart:
    def __init__(self, inventory, items=None):
        self.inventory = inventory
        self.items = items if items is not None else {}

    def add(self, sku, unit_price, qty=1):
        self.inventory.reserve(sku, qty)
        p, q = self.items.get(sku, (unit_price, 0))
        self.items[sku] = (p, q + qty)

    def remove(self, sku, qty=1):
        p, q = self.items[sku]
        q -= qty
        if q == 0:
            del self.items[sku]
        self.inventory.release(sku, qty)

    def total(self, discount_pct=0):
        sub = sum(p * q for p, q in self.items.values())
        return add_tax(apply_discount(sub, discount_pct))
