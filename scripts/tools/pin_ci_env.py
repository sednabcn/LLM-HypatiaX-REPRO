import pathlib, re, sys
dry = "--dry-run" in sys.argv
PINS = {"HYPATIAX_DISABLE_HARDCODED": "1", "HYPATIAX_DISABLE_PROMPT_HINTS": "1",
        "HYPATIAX_R2_SIGN_FLIP": "0", "HYPATIAX_STRICT": "1"}
for f in sorted(pathlib.Path(".github/workflows").glob("*.yml")):
    s = f.read_text()
    missing = {k: v for k, v in PINS.items() if not re.search(rf"^\s+{k}:", s, re.M)}
    if not missing:
        print("ok     ", f.name); continue
    lines = "".join(f'  {k}: "{v}"\n' for k, v in missing.items())
    if re.search(r"^env:\s*$", s, re.M):
        new = re.sub(r"^(env:\s*\n)", lambda m: m.group(1) + lines, s, count=1, flags=re.M)
    else:
        assert re.search(r"^jobs:", s, re.M), f"no jobs: in {f}"
        new = re.sub(r"^(jobs:)", lambda m: "env:\n" + lines + "\n" + m.group(1), s, count=1, flags=re.M)
    print("patched", f.name, list(missing))
    if not dry: f.write_text(new)
