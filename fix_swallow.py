import re, sys, pathlib
dry = "--dry-run" in sys.argv
pat = re.compile(r"^(\s*)except Exception:\s*\n\1\s+pass\b.*$", re.M)
for f in pathlib.Path("hypatiax").rglob("*.py"):
    s = f.read_text()
    n = len(pat.findall(s))
    if not n: continue
    new = pat.sub(lambda m: f"{m.group(1)}except Exception as _e:\n"
        f"{m.group(1)}    import logging, os\n"
        f"{m.group(1)}    logging.getLogger(__name__).warning('swallowed: %r', _e)\n"
        f"{m.group(1)}    if os.environ.get('HYPATIAX_STRICT') == '1': raise", s)
    print(f, n)
    if not dry: f.write_text(new)
