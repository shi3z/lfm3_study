def parse_kv(s):
    out = {}
    if not s:
        return out
    for part in s.split(','):
        part = part.strip()
        if not part:
            continue
        if '=' not in part:
            continue
        k, v = part.split('=', 1)
        k = k.strip()
        v = v.strip()
        if v:
            out[k] = int(v)
    return out
