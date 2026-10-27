def apply_discount(price, pct):
    """Return price after pct percent discount, rounded to 2 decimals."""
    return round(price * (1 - pct / 100), 2)


def add_tax(price, rate=0.08):
    return round(price * (1 + rate), 2)
