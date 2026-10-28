import ast, glob, json

K = {"h", "hbar", "c", "k_B", "k", "N_A", "g_n", "m_e", "q_e", "epsilon0", "mu0"}
n = hits = 0
for f in sorted(glob.glob("p2/pure_llm_*.jsonl")):
    for ln in open(f):
        if not ln.strip():
            continue
        r = json.loads(ln)
        for i, src in enumerate(r.get("candidate_formulas") or []):
            n += 1
            try:
                t = ast.parse(src)
            except SyntaxError:
                print(r["equation"], r["seed"], i, "SYNTAXERR")
                continue
            fn = next((x for x in ast.walk(t) if isinstance(x, ast.FunctionDef)), None)
            if fn is None:
                continue
            args = {a.arg for a in fn.args.args}
            stored = {x.id for x in ast.walk(fn) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)}
            loaded = {x.id for x in ast.walk(fn) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)}
            leak = (loaded & K) - args - stored
            if leak:
                hits += 1
                print(r["equation"], r["seed"], i, sorted(leak))
print("candidates checked:", n, "| using a prompt constant without defining it:", hits)
