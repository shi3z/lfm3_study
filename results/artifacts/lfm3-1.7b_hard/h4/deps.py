class CycleError(Exception):
    def __init__(self, cycle):
        super().__init__(f"cycle: {cycle}")
        self.cycle = cycle


def _find_cycle(graph):
    """Return a list of nodes forming a cycle in `graph` (node -> list of dependencies),
    or None if no cycle exists."""
    visited = set()
    stack = []

    def dfs(node):
        stack.append(node)
        for dep in graph.get(node, []):
            if dep not in graph:
                continue
            if dep in stack:
                idx = stack.index(dep)
                return stack[idx:]
            if dep not in visited:
                res = dfs(dep)
                if res is not None:
                    return res
        stack.pop()
        return None

    for node in graph:
        if node not in visited:
            res = dfs(node)
            if res is not None:
                return res
    return None


def resolve(graph):
    """
    Return a topological ordering of nodes in `graph` where for each node,
    its dependencies (the values in graph[node]) appear before the node itself.
    Nodes that appear only as dependencies (not as keys) are included.
    If multiple valid orderings exist, the one with the smallest node id
    (alphabetically) at each step is returned.
    Raises CycleError(cycle=...) if `graph` contains a cycle (including self-loops).
    """
    # collect all nodes: keys and every value (dependency)
    nodes = set(graph.keys())
    for deps in graph.values():
        nodes.update(deps)

    # indegree = number of dependencies each node has
    indegree = {node: len(graph.get(node, [])) for node in nodes}

    # reverse adjacency: for each node, which nodes depend on it (i.e., list of nodes that have it in their deps)
    rev = {node: [] for node in nodes}
    for node, deps in graph.items():
        for dep in deps:
            if dep in rev:
                rev[dep].append(node)

    # Kahn's algorithm: start with nodes having indegree 0, pick smallest alphabetically each round
    queue = sorted([n for n, deg in indegree.items() if deg == 0])
    result = []
    while queue:
        node = queue.pop(0)
        result.append(node)
        for dependent in rev.get(node, []):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                # insert in sorted position to keep alphabetical order
                idx = next((i for i, x in enumerate(queue) if x > dependent), len(queue))
                queue.insert(idx, dependent)
    if len(result) != len(nodes):
        cycle = _find_cycle(graph)
        if cycle is None:
            raise CycleError(list(nodes))
        else:
            raise CycleError(cycle)
    return result
