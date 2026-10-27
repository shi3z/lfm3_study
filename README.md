# lfm3_study — can a ~2B LFM3 model drive Claude Code?

A small, honest smoke test: run **Claude Code** with a locally served small model as its backend and see whether the
model can actually do agentic coding chores (read files → edit → run tests → iterate).

Models tried (all served locally with Hugging Face `transformers`, bf16, one A100 80GB):

| Model | Params | Notes |
|---|---|---|
| [LiquidAI/LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B) | 1.73B | text, post-trained, thinking on; model card targets local agents / tool calling |
| [LiquidAI/LFM3-Omni-2B](https://huggingface.co/LiquidAI/LFM3-Omni-2B) | 2.17B | omni-modal, non-reasoning; used in text mode, greedy (easy suite only) |
| [Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) | ~4B | baseline for comparison, thinking on |

Other models in the [LFM3 collection](https://huggingface.co/collections/LiquidAI/lfm3) were **not** run:
`LFM3-1.7B-Base` (not post-trained), `d1-2B` / `d1-Omni-2B` (single-forward-pass "decision" models; the card says
"not a chat model"), and `LFM3-VL-2B` (card: "not recommended for coding").

## TL;DR

| Suite | LFM3-1.7B | Qwen3.5-4B | LFM3-Omni-2B |
|---|---|---|---|
| Easy (5 tasks) | **5 / 5** | 2 / 5 (see timeout caveat) | 1 / 5 |
| Hard (5 tasks) | **4 / 5** | 0 / 5 | not run |
| Generation speed (HF `generate`, A100) | ~100 tok/s | ~29 tok/s | – |
| Calls that hit the 20,000-token cap | 1 of 114 | 9 of 57 | – |

* **LFM3-1.7B (thinking on, card-recommended sampling) works as a Claude Code backend for small, well-specified tasks.**
  It fixed multi-file bugs, implemented a topological sort, extended a CLI, and answered a repo-exploration question,
  usually in 15–60 s per easy task and 2.5–6 min per hard task.
* **LFM3-Omni-2B (non-reasoning) does not**: it called non-existent tools, overwrote test files with weaker ones, and
  looped on identical failed calls.
* **Qwen3.5-4B, in this particular setup, did worse than the smaller LFM3-1.7B** — mostly because of runaway
  generations (a single reply running to the 20,000-token cap, ~8–10 min each) and, in 3 of 5 hard tasks (h2–h4),
  *reporting success that the files on disk did not support* (h2 and h4: no code written at all). See caveats: this is one trial per task and says little about Qwen's quality in
  other harnesses.
* This does **not** reproduce or refute the vendors' benchmark numbers (SWE-bench Verified etc.); the tasks here are
  tiny and synthetic. See [Limitations](#limitations--things-that-could-change-the-picture).

## Results in detail

Wall time = time from launching `claude -p` until it exits or is killed (includes Claude Code overhead, tool
execution, and all model generation). Timeouts: **400 s (easy), 900 s (hard)**. Full CSV: [`results/summary.csv`](results/summary.csv).

### Easy suite (task details: [`bench/TASKS.md`](bench/TASKS.md))

| Task | What it asks | LFM3-1.7B | Qwen3.5-4B | LFM3-Omni-2B |
|---|---|---|---|---|
| t1 | fix `Stack.pop` (FIFO→LIFO) using the failing test | PASS 43 s | PASS (killed at 400 s timeout)¹ | FAIL 18 s |
| t2 | create `fib(n)` in a new file and run it | PASS 16 s | FAIL (timeout; file never created) | PASS 10 s |
| t3 | rename a function across 3 files | PASS 40 s | FAIL (timeout; `main.py` left half-edited, broken) | FAIL 11 s (only renamed in the definition file) |
| t4 | implement an LRU cache against a given test | PASS 32 s | FAIL (timeout; `lru.py` still the empty stub) | FAIL 32 s (overwrote the test, broken impl) |
| t5 | make `parse_kv` pass 4 tests | PASS 35 s | PASS (killed at 400 s timeout)¹ | FAIL 24 s (clobbered `parse.py` with test code) |

¹ The process was killed by the timeout but the files were already correct when the check ran. The real time-to-done is unknown (≤ 400 s).

Test-file integrity (easy suite): LFM3-1.7B left `test_stack.py`/`test_parse.py` untouched and **reformatted
`test_lru.py`** (identical assertions; added a `sys.path` line and a `__main__` block). Its `lru.py` also passes the
*original* test. Qwen3.5-4B edited no test files. LFM3-Omni-2B rewrote two test files.

### Hard suite

| Task | What it asks | LFM3-1.7B | Qwen3.5-4B |
|---|---|---|---|
| h1 | fix 4 seeded bugs across a 3-file package; tests must stay byte-identical | PASS 351 s | FAIL 900 s (timeout; also on a clean re-run²) |
| h2 | implement an expression evaluator (precedence, right-assoc `^`, unary minus, errors) — 22 hidden tests | FAIL 282 s (no file written; partial parser printed as plain text) | FAIL 303 s (zero tool calls; final message claimed "All 57 tests pass"; `expr.py` untouched) |
| h3 | add `stopwords`/`min_length` + CLI flags (`--json` …) — 7 hidden tests | PASS 154 s | FAIL 502 s (claimed success; `top_words` signature never changed → `TypeError`) |
| h4 | topological sort with cycle detection — 7 hidden tests | PASS 258 s | FAIL 195 s (ran `python deps.py`, no code written, reported "All tests pass") |
| h5 | locate an env var / default / reader function / callers in a 12-file repo and write `ANSWER.txt` | PASS 309 s | FAIL 900 s (timeout; no `ANSWER.txt`) |

² The first Qwen h1 run overlapped with a leftover benchmark process from an earlier aborted run that was still
sending requests to the same server, so its timing is unreliable. h1 was re-run alone on a clean server and failed the
same way (still generating at the 900 s timeout). `results/artifacts/qwen3.5-4b_hard_h1_clean_rerun/`.

Side effect worth knowing: while working on h4, LFM3-1.7B created a full Python virtualenv inside `tests/venv/`
(removed from this repo's artifacts because it is third-party files).

### Generation statistics (from the shim logs, `results/logs/`)

| | LFM3-1.7B | Qwen3.5-4B |
|---|---|---|
| Model calls during both suites | 114 | 57 |
| Prompt tokens (sum) | 1.61 M | 0.67 M |
| Output tokens (sum) | 104 K | 203 K |
| Max output tokens in a single call | 20,000 (1×) | 20,000 (9×) |
| Throughput | ~100 tok/s (probe: 600 new tokens in 6 s, short prompt) | 28.9 tok/s (mean over 55 timed calls, 12–15K-token prompts, includes prefill) |

LFM3-1.7B's full-run log has no per-call timing (the timer was added later), so its throughput comes from a separate
probe on the same GPU and is **not** apples-to-apples with Qwen's in-run mean. Claude Code's own system prompt + tool
definitions are ≈ 11K tokens, so every call carries at least that much prefill.

## How the benchmark works

```
claude -p "<task prompt>"  ──Anthropic Messages API──▶  shim/anthropic_shim_server.py  ──▶  transformers model.generate()
   (Claude Code 2.1.312)        POST /v1/messages          (FastAPI, SSE, tool_use ⇄ XML)      (bf16, one GPU, no batching)
```

1. **Shim server** (`shim/anthropic_shim_server.py`): a minimal Anthropic-Messages-compatible endpoint
   (`/v1/messages`, `/v1/messages/count_tokens`, streaming and non-streaming).
   * Anthropic `tools` → HF chat-template `tools=`; `tool_use` / `tool_result` blocks ⇄ the models' XML tool-call
     format (`<tool_call><function=…><parameter=…>…`, which LFM3 and Qwen3.5 share).
   * Thinking text (everything up to the last `</think>`) is stripped from the reply and not replayed in history.
   * Generation is run to completion, then replayed as SSE (no token-level streaming).
   * `max_new_tokens = min(request max_tokens, 20000, context − prompt)`; context window 64K.
2. **Claude Code** is pointed at it with `ANTHROPIC_BASE_URL=http://127.0.0.1:8321`, a dummy API key, and
   `--dangerously-skip-permissions` in a throw-away directory per task.
3. **Runners** `bench/run_easy.sh`, `bench/run_hard.sh` create each task directory, run `claude -p`, then execute an
   objective check (pytest / grep) and print `task PASS|FAIL <seconds>`.
4. **Sampling** (from each model card): LFM3-1.7B — its `generation_config.json` (temperature 0.1, top_k 50,
   repetition_penalty 1.1), thinking on. Qwen3.5-4B — the card's "thinking, precise coding" setting (temperature 0.6,
   top_p 0.95, top_k 20; presence_penalty not available in `generate`, card value for this mode is 0). LFM3-Omni-2B —
   greedy, as its card recommends for text.

### Reproduce

```bash
# env: transformers>=5.21, torch, torchvision, fastapi, uvicorn, accelerate, pillow, soundfile, librosa;
#      for Qwen3.5 also `pip install flash-linear-attention` (otherwise very slow fallback kernels)
LFM_MODEL=LiquidAI/LFM3-1.7B LFM_KIND=text LFM_CTX=65536 python shim/anthropic_shim_server.py &   # listens on :8321
# Qwen: LFM_MODEL=Qwen/Qwen3.5-4B LFM_KIND=text LFM_SAMPLE='{"do_sample":true,"temperature":0.6,"top_p":0.95,"top_k":20,"repetition_penalty":1.0}'
# Omni: LFM_MODEL=LiquidAI/LFM3-Omni-2B LFM_KIND=omni
PY=python3 bench/run_easy.sh      # → bench/runs_easy/
PY=python3 bench/run_hard.sh      # → bench/runs_hard/   (ONLY=h1 to run a single task)
```

Raw material: `results/artifacts/<model>_<suite>/<task>/` holds each run's final workspace, the agent's final message
(`out.txt`) and the check output (`check.txt`); `results/logs/` holds the shim logs (one line per model call with
input/output token counts and, for the later runs, seconds) and the runner outputs.

## Limitations / things that could change the picture

* **n = 1 per task per model.** Both models sample (T = 0.1 and 0.6), so rerunning would give different numbers.
  5 + 5 tasks is far too few for confidence intervals.
* **Home-made harness.** I wrote the API shim and the tasks. Qwen3.5 + thinking + Claude Code's long prompt may behave
  better under vLLM/SGLang with the official reasoning/tool parsers, a presence penalty, or a different
  `max_tokens`. The 20,000-token runaways in particular may be sensitive to sampling settings and the missing
  causal-conv1d kernel (reference implementation fallback; numerically fine, just slow).
* **Timeouts favour fast models**: 400 s / 900 s per task. Slow models fail by running out of clock even when they
  would eventually have made progress; the "PASS 400 s" rows show this cuts both ways.
* **Methodology bug history (fixed before the numbers above):** my first LFM3-1.7B hard-suite run went 0/5 because the
  shim capped `max_new_tokens` at 4096 and thinking replies were truncated mid-thought, and one hidden test (h3's CLI
  case) had a wrong expectation. After both were fixed, the full hard suite was re-run and is what is reported. The
  LFM3-Omni-2B easy-suite numbers come from the earlier shim version (4096-token cap, 32K context); its failures were
  visibly model-driven (hallucinated tools, overwritten tests), not truncation.
* **Shared GPU.** The A100 was shared with unrelated jobs (≈ 59–67 GB of its 80 GB in use by other processes), so
  absolute speeds are indicative only.
* **Hidden tests are mine** and the h5 check is string matching.
* **Not a test of the vendors' claims.** E.g. LFM3-1.7B's model card reports SWE-bench Verified 43.4 (OpenCode),
  BFCL V4 71.4; none of that was measured here.

## Versions

Claude Code 2.1.312 · transformers 5.21.0 · torch 2.14.1+cu130 · flash-linear-attention 0.6.0 (Qwen runs) ·
NVIDIA A100 80GB PCIe · benchmark run 2026-10-27/28.
