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
