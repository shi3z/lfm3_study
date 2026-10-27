# Task definitions

Every task runs in a fresh, empty directory. The agent is `claude -p "<prompt>" --dangerously-skip-permissions`
(Claude Code 2.1.312) and gets no hints beyond the prompt. The prompts were written in Japanese; English
translations are given for reference (the Japanese text in `run_easy.sh` / `run_hard.sh` is what was actually sent).

Success is decided by an **objective, automatic check** after the agent exits (or is killed by the timeout).
For implementation tasks in the hard suite the check uses **hidden tests** (`bench/hidden/`) that the agent never sees.

## Easy suite (`run_easy.sh`) — 1–2 step edits, visible tests, 400 s timeout, `--max-turns 15`

| ID | Setup | Prompt (EN) | Check |
|---|---|---|---|
| t1 | `stack.py` whose `pop()` uses `pop(0)` (FIFO, should be LIFO); `test_stack.py` | "test_stack.py fails. Run pytest, find the cause, and fix stack.py." | `pytest test_stack.py` passes |
| t2 | empty dir | "Create hello.py with a function fib(n) returning the n-th Fibonacci number; fib(10)==55. Run the file to verify." | importing `hello.fib` gives fib(0)=0, fib(1)=1, fib(10)=55 |
| t3 | `pkg/util.py` defines `calc_total`; used in `main.py` and `other.py` | "Rename calc_total in pkg/util.py to compute_sum and update every usage." | no occurrence of `calc_total` left; `main.py` prints 6; `other.f()==4` |
| t4 | `lru.py` is an empty class with a docstring; `test_lru.py` (capacity 2, eviction order, overwrite) | "Implement LRUCache in lru.py and make test_lru.py pass." | `pytest test_lru.py` passes (runs whatever `test_lru.py` is in the directory — see note) |
| t5 | `parse_kv` in `parse.py` fails on spaces / empty / trailing comma; `test_parse.py` with 4 tests | "Fix parse_kv in parse.py so all tests in test_parse.py pass. Verify with pytest." | `pytest test_parse.py` passes |

Note on t4/t5: the easy-suite check just runs the `test_*.py` found in the directory, so a model *could* pass by
editing the tests. I diffed the test files afterwards (results in the README):
LFM3-1.7B left `test_stack.py` and `test_parse.py` untouched and **reformatted `test_lru.py`** (same assertions, plus a
`sys.path` line and a `__main__` block); I re-ran the *original* `test_lru.py` against its `lru.py` and it passes.
Qwen3.5-4B left all three untouched. LFM3-Omni-2B rewrote `test_lru.py` and `test_parse.py` with its own weaker tests.
The hard suite's h1 compares the test file byte-for-byte; h2–h4 run hidden tests copied in after the agent finishes.

## Hard suite (`run_hard.sh`) — multi-file / from-scratch work, 900 s timeout, `--max-turns 40`

| ID | Setup | Prompt (EN) | Check |
|---|---|---|---|
| h1 | `shop/` package (`pricing.py`, `inventory.py`, `cart.py`) with **4 seeded bugs** (discount divides pct by 10; off-by-one in `reserve`; shared mutable default `items={}`; `remove` leaves qty-0 entries) and `tests/test_shop.py` (7 tests, 5 failing) | "tests/test_shop.py has several failures. Run pytest, find the causes and fix all bugs in the shop/ package. Do not change the tests." | test file byte-identical to the original **and** `pytest tests` passes |
| h2 | `expr.py` with `evaluate(s)` raising `NotImplementedError` | "Implement evaluate in expr.py: + - * / ^ (right-assoc, 2^3^2=512, 2^-1=0.5), parentheses, unary minus, decimals. Malformed input (empty, unbalanced parentheses, missing operator, unknown char, division by zero) must raise ValueError. Write your own tests and verify with pytest." | hidden `test_expr.py`: 14 valid expressions + 8 error cases (22 tests) |
| h3 | `wordfreq.py` with `top_words(text, n=10)` and a trivial CLI | "Extend wordfreq.py. (1) `top_words(text, n=10, stopwords=None, min_length=1)`: exclude stopwords (a set) and words shorter than min_length; ties ordered alphabetically. (2) CLI: `python wordfreq.py FILE [--top N] [--stopwords a,b,c] [--min-length K] [--json]`; with `--json` print `[[word,count],...]`; otherwise keep the old `word<TAB>count` output." | hidden `test_wf.py` (7 tests incl. two CLI subprocess tests) |
| h4 | `deps.py` with `CycleError` and a stub `resolve(graph)` | "Implement resolve(graph): topological order where dependencies come first; nodes that only appear as dependencies are included; ties broken alphabetically; raise CycleError(cycle=…) on cycles including self-loops. Write tests yourself and verify." | hidden `test_deps.py` (7 tests) |
| h5 | small app (`app/core`, `app/api`, `app/utils`, 12 files) with several env vars; one is the request time budget, read by `get_request_budget()` and used by two modules; a decoy module calls a different setting | "In this repo, find the env var that sets the per-request time limit (seconds), its default value, the function that reads it, and every module file that calls that function. Write the result to ANSWER.txt." | `ANSWER.txt` exists and contains `APP_BUDGET_S`, `12.5`, `get_request_budget`, `handlers.py`, `health.py`, and does **not** mention the decoy `client.py` |

## Why these tasks

They are deliberately ordinary agentic-coding chores (read → edit → run tests → iterate). They are *not* meant to
reproduce SWE-bench-style difficulty; they test whether a ~2B model can survive Claude Code's ~11K-token system prompt
and tool protocol and still do useful work. The sample is tiny (5+5 tasks, one trial each) — treat results as a smoke
test, not a leaderboard.
