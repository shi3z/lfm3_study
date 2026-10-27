def fib(n):
    """Return the n-th Fibonacci number (0-indexed).

    fib(0) -> 0
    fib(1) -> 1
    fib(10) -> 55
    """
    if n < 0:
        raise ValueError("n must be a non-negative integer")
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b if n >= 1 else a


if __name__ == "__main__":
    # Quick sanity checks
    assert fib(0) == 0
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(10) == 55
    print(f"fib(10) = {fib(10)}")
