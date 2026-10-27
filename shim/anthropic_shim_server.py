"""Anthropic Messages API shim over LFM3-Omni-2B (text mode) for Claude Code."""
import json, re, time, uuid, threading, sys
import torch
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from transformers import AutoModelForMultimodalLM, AutoModelForCausalLM, AutoProcessor, AutoTokenizer

import os
MODEL = os.environ.get("LFM_MODEL", "LiquidAI/LFM3-Omni-2B")  # HF id or local dir
TEXT = os.environ.get("LFM_KIND", "omni") == "text"
THINK = os.environ.get("LFM_THINK", "1") == "1"
SAMPLE = json.loads(os.environ.get("LFM_SAMPLE", "{}"))
MAX_CTX = int(os.environ.get("LFM_CTX", "32768"))
dev = "cuda"
_cls = AutoModelForCausalLM if TEXT else AutoModelForMultimodalLM
model = _cls.from_pretrained(MODEL, dtype=torch.bfloat16, device_map=dev, trust_remote_code=True).eval()
processor = (AutoTokenizer if TEXT else AutoProcessor).from_pretrained(MODEL, trust_remote_code=True)
lock = threading.Lock()
app = FastAPI()

CALL_RE = re.compile(r"<tool_call>\s*<function=([^>\n]+)>(.*?)</function>\s*</tool_call>", re.DOTALL)
PARAM_RE = re.compile(r"<parameter=([^>\n]+)>\n?(.*?)\n?</parameter>", re.DOTALL)


def parse_calls(text):
    calls = []
    for name, body in CALL_RE.findall(text):
        args = {}
        for k, v in PARAM_RE.findall(body):
            try:
                args[k] = json.loads(v)
            except json.JSONDecodeError:
                args[k] = v
        calls.append((name.strip(), args))
    return calls


def blocks(c):
    return [{"type": "text", "text": c}] if isinstance(c, str) else c


def to_conv(body):
    conv = []
    sys_p = body.get("system")
    if isinstance(sys_p, list):
        sys_p = "\n".join(b.get("text", "") for b in sys_p)
    if sys_p:
        conv.append({"role": "system", "content": [{"type": "text", "text": sys_p}]})
    for m in body["messages"]:
        texts, calls, results = [], [], []
        for b in blocks(m["content"]):
            t = b["type"]
            if t == "text":
                texts.append(b["text"])
            elif t == "tool_use":
                calls.append({"type": "function", "function": {"name": b["name"], "arguments": b["input"]}})
            elif t == "tool_result":
                c = b.get("content", "")
                if isinstance(c, list):
                    c = "\n".join(x.get("text", "") for x in c)
                results.append(str(c))
        if m["role"] == "assistant":
            msg = {"role": "assistant", "content": [{"type": "text", "text": "\n".join(texts)}]}
            if calls:
                msg["tool_calls"] = calls
            conv.append(msg)
        else:
            for r in results:
                conv.append({"role": "tool", "content": r})
            if texts:
                conv.append({"role": "user", "content": [{"type": "text", "text": "\n".join(texts)}]})
    tools = [{"type": "function", "function": {
        "name": t["name"], "description": t.get("description", ""),
        "parameters": t.get("input_schema", {"type": "object", "properties": {}})}}
        for t in body.get("tools", [])] or None
    return conv, tools


def flat(conv):
    for m in conv:
        if isinstance(m.get("content"), list):
            m["content"] = "\n".join(p.get("text", "") for p in m["content"])
    return conv


def encode(body):
    conv, tools = to_conv(body)
    kw = dict(tools=tools, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt")
    if TEXT:
        return processor.apply_chat_template(flat(conv), enable_thinking=THINK, **kw).to(dev)
    return processor.apply_chat_template(conv, **kw).to(dev)


def generate(body):
    t0 = time.time()
    inputs = encode(body)
    n_in = inputs["input_ids"].shape[1]
    max_new = min(body.get("max_tokens", 1024), 20000, max(64, MAX_CTX - n_in))
    with lock, torch.no_grad():
        if TEXT:
            out = model.generate(**inputs, max_new_tokens=max_new, **SAMPLE)
            seq = out[0, n_in:]
            n_out = int(seq.shape[0])
            text = processor.decode(seq, skip_special_tokens=True)
        else:
            out = model.generate(**inputs, max_new_tokens=max_new, generation_mode="text")
            n_out = int(out.sequence_lengths[0]) - n_in
            text = processor.decode(out.sequences[0, n_in:out.sequence_lengths[0]], skip_special_tokens=True)
    text = text.split("</think>")[-1] if "</think>" in text else text
    text = text.replace("<think></think>", "").strip()
    print(f"[gen] {time.time()-t0:.0f}s in={n_in} out={n_out} text={text[:300]!r}", flush=True)
    return text, n_in, n_out


def to_content(text):
    calls = parse_calls(text)
    pre = CALL_RE.split(text)[0].strip() if calls else text
    content = [{"type": "text", "text": pre}] if pre else []
    for name, args in calls:
        content.append({"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": name, "input": args})
    if not content:
        content = [{"type": "text", "text": " "}]
    return content, bool(calls)


def sse(ev, data):
    return f"event: {ev}\ndata: {json.dumps(data)}\n\n"


@app.post("/v1/messages")
async def messages(req: Request):
    body = await req.json()
    try:
        text, n_in, n_out = await __import__("asyncio").to_thread(generate, body)
    except Exception as e:  # context overflow etc.
        import traceback; traceback.print_exc()
        return JSONResponse({"type": "error", "error": {"type": "invalid_request_error", "message": str(e)}}, status_code=400)
    content, has_tool = to_content(text)
    msg = {"id": "msg_" + uuid.uuid4().hex[:20], "type": "message", "role": "assistant",
           "model": body.get("model", "lfm3-omni-2b"), "content": content,
           "stop_reason": "tool_use" if has_tool else "end_turn", "stop_sequence": None,
           "usage": {"input_tokens": n_in, "output_tokens": n_out}}
    if not body.get("stream"):
        return JSONResponse(msg)

    def gen():
        yield sse("message_start", {"type": "message_start", "message": {**msg, "content": [], "stop_reason": None,
                                    "usage": {"input_tokens": n_in, "output_tokens": 1}}})
        for i, b in enumerate(content):
            if b["type"] == "text":
                yield sse("content_block_start", {"type": "content_block_start", "index": i, "content_block": {"type": "text", "text": ""}})
                yield sse("content_block_delta", {"type": "content_block_delta", "index": i, "delta": {"type": "text_delta", "text": b["text"]}})
            else:
                yield sse("content_block_start", {"type": "content_block_start", "index": i, "content_block": {**b, "input": {}}})
                yield sse("content_block_delta", {"type": "content_block_delta", "index": i, "delta": {"type": "input_json_delta", "partial_json": json.dumps(b["input"])}})
            yield sse("content_block_stop", {"type": "content_block_stop", "index": i})
        yield sse("message_delta", {"type": "message_delta", "delta": {"stop_reason": msg["stop_reason"], "stop_sequence": None}, "usage": {"output_tokens": n_out}})
        yield sse("message_stop", {"type": "message_stop"})
    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/v1/messages/count_tokens")
async def count(req: Request):
    body = await req.json()
    return {"input_tokens": int(encode(body)["input_ids"].shape[1])}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8321, log_level="warning")
