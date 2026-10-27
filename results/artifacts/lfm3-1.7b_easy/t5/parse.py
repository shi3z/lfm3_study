def parse_kv(s):
    out={}
    for part in s.split(','):
        part = part.strip()
        if not part:
            continue
        k, v = part.split('=', 1)
        out[k.strip()] = int(v.strip())
    return out
