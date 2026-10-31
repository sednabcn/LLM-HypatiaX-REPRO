#!/usr/bin/env bash
# Pipeline / git consistency checks. Run from the repo root. Exit 1 on any FAIL.
fail=0
chk() { if [ "$2" = "0" ]; then echo "ok   $1"; else echo "FAIL $1"; fail=1; fi; }

# 1. dry-run step count equals _STEP_ORDER length
want=$(grep -E '^_STEP_ORDER=' run_all.sh | sed 's/.*="//; s/"$//' | wc -w)
got=$(bash run_all.sh --dry-run 2>&1 | grep -c 'STEP:')
[ "$want" = "$got" ]; chk "dry-run steps ($got) == _STEP_ORDER ($want)" $?

# 2. every run line is in _STEP_ORDER and vice versa
grep -E '^_STEP_ORDER=' run_all.sh | sed 's/.*="//; s/"$//' | tr ' ' '\n' | sort -u > /tmp/order.txt
grep -oE '^run [a-z0-9_]+' run_all.sh | awk '{print $2}' | sort -u > /tmp/runs.txt
if diff -q /tmp/order.txt /tmp/runs.txt >/dev/null; then echo "ok   run lines match _STEP_ORDER"; else echo "INFO run-line names differ from _STEP_ORDER (generated names such as supp* are expected; inspect diff)"; fi
diff /tmp/order.txt /tmp/runs.txt | head -10

# 3. controlled flags
grep -qE 'export HYPATIAX_R2_SIGN_FLIP' run_all.sh; chk "SIGN_FLIP exported in run_all.sh" $?
grep -qE 'HYPATIAX_STRICT.*(!=|-ne)' run_all.sh; chk "STRICT==1 asserted in run_all.sh" $?

# 4. freeze tag and duplicate commits
git rev-parse -q --verify freeze-pre-audit >/dev/null; chk "freeze-pre-audit tag exists" $?
a=$(git show 7d45ebc 2>/dev/null | git patch-id --stable | cut -d' ' -f1)
b=$(git show 81662dd 2>/dev/null | git patch-id --stable | cut -d' ' -f1)
if [ -n "$a" ] && [ "$a" = "$b" ]; then echo "INFO 7d45ebc and 81662dd have identical patches (duplicate)"; \
else echo "INFO 7d45ebc / 81662dd patches differ or missing (a=$a b=$b)"; fi

# 5. deleted files by top directories (nothing the pipeline needs removed?)
echo "--- deletions since freeze (top dirs) ---"
git diff --diff-filter=D --name-only freeze-pre-audit HEAD | awk -F/ '{print $1"/"$2}' | sort | uniq -c | sort -rn | head -12
echo "--- deleted files still referenced by run_all.sh ---"
git diff --diff-filter=D --name-only freeze-pre-audit HEAD | while read -r f; do
  b=$(basename "$f"); grep -q "$b" run_all.sh && echo "REFERENCED: $f" && fail=1
done

# 6. steps that cannot honour seed / noise
echo "INFO hybrid_all_domains uses ExperimentProtocolAll (ignores seed/noiseless): no seed or noise claims from that step"

exit $fail
