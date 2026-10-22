#!/usr/bin/env bash
# Run from the OLD repo root (LLM-HypatiaX-REPRO):   bash probe_old.sh
# Read-only. Writes audit_out/probe_old.txt (paste or attach that file).
mkdir -p audit_out
OUT=audit_out/probe_old.txt
S=hypatiax/experiments/benchmarks/run_comparative_suite_benchmark_v2.py
P=hypatiax/core/base_pure_llm/baseline_pure_llm_defi_discovery.py

{
echo "=== 1. SIGN-FLIP: does the suite report max(r2, r2_flip)? ==="
grep -n "r2_flip\|ss_flip\|_safe_r2\|sign-flip\|sign_flip" "$S" | head -40
echo "--- lines 476-500"; sed -n 476,500p "$S"
echo "--- lines 1046-1070"; sed -n 1046,1070p "$S"

echo; echo "=== 2. BYPASS BRANCHES: what survives when both flags are set? ==="
grep -n "_try_hardcoded_formula\|disable_hc\|disable_hints\|bypass_kind\|DISABLE_" "$P" | head -60
echo "--- lines 340-470"; sed -n 340,470p "$P"

echo; echo "=== 3. DOES THE DESCRIPTION REACH THE PROMPT? ==="
grep -n "description" "$P" | head -40

echo; echo "=== 4. TIMING CENSUS (fast + success + flag None/False = unflagged bypass) ==="
python - <<'EOF'
import json, glob, collections as C
c = C.Counter()
for f in glob.glob("hypatiax/data/results/**/protocol_core_*.json", recursive=True):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    for t in d.get("tests", []):
        for m, r in t.get("results", {}).items():
            tm = r.get("time")
            fast = isinstance(tm, (int, float)) and tm < 0.05
            hc = (r.get("metadata") or {}).get("is_hardcoded")
            c[(m, "fast" if fast else "slow", hc, bool(r.get("success")))] += 1
for k, v in sorted(c.items(), key=str):
    print(v, k)
EOF

echo; echo "=== 5. FORMULA TEXT IN TEST DESCRIPTIONS (unique) ==="
python - <<'EOF'
import json, glob, re
seen = {}
for f in glob.glob("hypatiax/data/results/**/protocol_core_*.json", recursive=True):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    for t in d.get("tests", []):
        s = t.get("description", "")
        seen[s] = bool(re.search(r"[=*^]|exp\(", s))
bad = sorted(s for s, b in seen.items() if b)
print(len(bad), "of", len(seen), "unique descriptions contain formula-like text")
for s in bad[:60]:
    print("  ", s[:120])
EOF

echo; echo "=== 6. HISTORY: when did provenance / clean flags appear? ==="
git log -S"bypass_kind" --format="%h %ad %s" --date=short -- hypatiax | tail -3
git log -S"HYPATIAX_DISABLE_HARDCODED" --format="%h %ad %s" --date=short -- hypatiax | tail -3

echo; echo "=== 7. EXISTING ABLATION (exp1_ablation) ==="
grep -nE "ARMS|ARM_|ablat|--arm|gate" hypatiax/experiments/benchmarks/exp1_ablation.py | head -40
head -c 600 hypatiax/data/results/ablation/exp1_ablation/provenance_map_exp1.json; echo

echo; echo "=== 8. HOW EACH RESULT WAS PRODUCED (run_all.sh) ==="
grep -nE "python3? +hypatiax/" run_all.sh | cut -c1-160 | head -120
} 2>&1 | tee "$OUT"

echo; echo "Saved to $OUT"
