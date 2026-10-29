import json, sys

KEYS = {"test_r2", "train_r2", "r2"}
CTX = ("equation", "name", "method", "system", "domain", "success", "status", "error")

def walk(o, path, out):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in KEYS and isinstance(v, float) and v == 0.0:
                ctx = {c: o[c] for c in CTX if c in o and not isinstance(o[c], (dict, list))}
                out.append(("/".join(map(str, path + [k])), ctx))
            walk(v, path + [k], out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, path + [i], out)

for fn in sys.argv[1:]:
    out = []
    walk(json.load(open(fn)), [], out)
    print("==", fn.split("/")[-1], len(out), "exact zeros")
    for p, c in out[:6]:
        print("  ", p, c)
