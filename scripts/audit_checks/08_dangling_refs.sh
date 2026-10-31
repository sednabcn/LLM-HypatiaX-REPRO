#!/usr/bin/env bash
# Referenced-but-missing scripts/workflows in a git ref. Ignores comment lines, scripts/archive and result data.
# Usage: REF=origin/master bash 08_dangling_refs.sh   (default REF=HEAD). Exit 1 if any missing.
REF="${REF:-HEAD}"
PAT='(\.github/(scripts|workflows)|scripts|hypatiax)/[A-Za-z0-9_./-]+\.(py|sh|yml|json)|\bci_[a-z0-9_]+\.yml'
hits=$(git grep -n -I -E "$PAT" "$REF" -- run_all.sh Makefile .github scripts ':!scripts/archive' ':!*.md' 2>/dev/null \
       | sed -E "s#^${REF}:##" | grep -vE '^[^:]+:[0-9]+:[[:space:]]*(#|//|"""|\*)')
paths=$(echo "$hits" | grep -oE '(\.github/(scripts|workflows)|scripts|hypatiax)/[A-Za-z0-9_./-]+\.(py|sh|yml|json)' | grep -v '^hypatiax/data/' | sort -u)
wfs=$(echo "$hits" | grep -oE '\bci_[a-z0-9_]+\.yml' | sort -u | sed 's#^#.github/workflows/#')
bad=0; n=0
for p in $paths $wfs; do
  n=$((n+1))
  if ! git cat-file -e "$REF:$p" 2>/dev/null; then
    bad=$((bad+1)); echo "MISSING $p"
    echo "$hits" | grep -F "$(basename "$p")" | cut -c1-150 | head -2 | sed 's/^/    ref: /'
  fi
done
echo "checked $n referenced paths at $REF; missing: $bad"
[ "$bad" = 0 ]
