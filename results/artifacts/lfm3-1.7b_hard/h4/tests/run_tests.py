import sys
sys.path.insert(0, '<ROOT>/runs_hard/h4')
sys.path.insert(0, '<ROOT>/runs_hard/h4/tests')
import test_deps

tests = [
    ('basic_topological_order', test_deps.test_basic_topological_order),
    ('diamond_pick_smallest_first', test_deps.test_diamond_pick_smallest_first),
    ('self_loop_raises', test_deps.test_self_loop_raises),
    ('mutual_cycle_raises', test_deps.test_mutual_cycle_raises),
    ('no_cycle_single_node', test_deps.test_no_cycle_single_node),
    ('cycle_entire_graph', test_deps.test_cycle_entire_graph),
    ('unknown_key_ignored', test_deps.test_unknown_key_ignored),
    ('multiple_possible_orders', test_deps.test_multiple_possible_orders_pick_minimal_at_each_step),
]

for name, fn in tests:
    try:
        fn()
        print(f'PASS: {name}')
    except Exception as e:
        print(f'FAIL: {name}: {e}')
