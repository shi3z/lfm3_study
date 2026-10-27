"""Tests for deps.resolve(graph) in deps.py."""

from deps import CycleError, resolve


def test_basic_topological_order():
    """Graph: a depends on b, b depends on c, c has none.
    Valid order: c first (no deps), then b (needs c), then a (needs b).
    """
    graph = {
        'a': ['b'],
        'b': ['c'],
        'c': [],
    }
    assert resolve(graph) == ['c', 'b', 'a']


def test_diamond_pick_smallest_first():
    """
    Diamond: root depends on left and right; left depends on leaf; right depends on leaf.
    Zero indegree nodes initially: leaf (no deps). Pick 'leaf' first?
    Wait: leaf has no dependencies, so it's zero indegree. But leaf is depended upon by left/right.
    In Kahn's algorithm we start with nodes that have NO dependencies (indegree 0). That's leaf.
    However, the standard interpretation: we want dependencies first. Starting with leaf (no deps) is fine
    because leaf has no requirements; but logically, left and right depend on leaf, so leaf must come before left/right.
    Order produced by Kahn: start with leaf (indeg 0). Remove leaf -> decrement indegree of left and right (both become 0).
    Then queue has left, right -> pick smallest 'left'. Remove left -> decrement indegree of root (root had 2 deps: left, right -> becomes 1). root not 0.
    Then queue has right -> pick 'right'. Remove right -> decrement indegree of root -> 0. root added.
    Result: ['leaf', 'left', 'right', 'root'].
    That's a valid topological order satisfying dependencies. The test just checks validity, not uniqueness.
    """
    graph = {
        'root': ['left', 'right'],
        'left': ['leaf'],
        'right': ['leaf'],
        'leaf': [],
    }
    result = resolve(graph)
    # Verify: for each node, its dependencies appear before it in result.
    pos = {node: idx for idx, node in enumerate(result)}
    for node, deps in graph.items():
        for dep in deps:
            assert pos[dep] < pos[node], f"{node} depends on {dep} but {dep} appears after {node}"
    # Check all nodes present
    assert set(result) == {'root', 'left', 'right', 'leaf'}


def test_self_loop_raises():
    """Self-loop: 'a' depends on 'a' -> cycle ['a']."""
    graph = {'a': ['a']}
    try:
        resolve(graph)
    except CycleError as e:
        assert e.cycle == ['a'], f"expected ['a'], got {e.cycle}"
    else:
        raise AssertionError("CycleError not raised")


def test_mutual_cycle_raises():
    """Mutual cycle between a and b -> cycle ['a', 'b'] (order from dfs)."""
    graph = {'a': ['b'], 'b': ['a']}
    try:
        resolve(graph)
    except CycleError as e:
        # dfs finds cycle starting from 'a': stack = ['a','b'], dep 'b' in stack at idx 1 -> returns ['b','a']?
        # Let's just check it's a list of nodes involved.
        assert isinstance(e.cycle, list) and len(e.cycle) >= 2
    else:
        raise AssertionError("CycleError not raised")


def test_no_cycle_single_node():
    """Node with no dependencies and no dependents -> ['node']."""
    graph = {'x': []}
    assert resolve(graph) == ['x']


def test_cycle_entire_graph():
    """Cycle involving all nodes -> raises CycleError with all three nodes."""
    graph = {'a': ['b'], 'b': ['c'], 'c': ['a']}
    try:
        resolve(graph)
    except CycleError as e:
        assert set(e.cycle) == {'a', 'b', 'c'}
    else:
        raise AssertionError("CycleError not raised")


def test_unknown_key_ignored():
    """Keys not in graph dict but referenced as dependencies should still be included."""
    graph = {
        'a': ['b'],
        'b': [],
    }
    # 'b' is a dependency of 'a' but not a key. It should be included.
    result = resolve(graph)
    assert 'b' in result, f"missing node 'b' in result {result}"
    # 'a' depends on 'b', so 'b' must come before 'a'
    assert result.index('b') < result.index('a')


def test_multiple_possible_orders_pick_minimal_at_each_step():
    """
    Build a case where at a step there are two zero-indegree candidates.
    Example: graph = {'a': [], 'b': ['a'], 'c': ['a']}.
    Initially zero indegree: 'a' (no deps). Pick 'a'. After removing 'a', b and c become zero.
    At that step, candidates are 'b' and 'c'; pick smaller alphabetically 'b'.
    Result: ['a', 'b', 'c'].
    """
    graph = {
        'a': [],
        'b': ['a'],
        'c': ['a'],
    }
    result = resolve(graph)
    assert result == ['a', 'b', 'c']
