#!/usr/bin/env python3
"""Adds leave-one-gate-out support to ci_runner_repro.yml (exact-match edits; aborts if the
file has drifted).  Usage: python3 scripts/option3/patch_runner_for_ablation.py [path]

  1. new input  ablate_gate  (default "none")
  2. HDS_ABLATE_GATE exported to every step (the code must read it)
  3. OUT_BASE moves to hypatiax/data/results/option3_ablation/<gate> for ablation runs, so
     results, checkpoints, commits and artifacts can never touch the baseline outputs
  4. concurrency group includes the gate, otherwise parallel ablations of the same
     experiment queue behind each other and GitHub cancels all but one pending run
"""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else ".github/workflows/ci_runner_repro.yml"
s = open(p).read()

def sub(old, new):
    global s
    assert s.count(old) == 1, f"expected exactly 1 match, found {s.count(old)}: {old[:80]!r}"
    s = s.replace(old, new)

sub('''        default: "fallback"

concurrency:''', '''        default: "fallback"

      ablate_gate:
        description: "Option 3 / Phase 3 leave-one-gate-out: gate to REMOVE (none = full HDS v50_2). Exported as HDS_ABLATE_GATE; results are isolated under hypatiax/data/results/option3_ablation/<gate>. The code must implement the toggle."
        required: false
        default: "none"

concurrency:''')
sub("group: ${{ github.workflow }}-${{ github.event.inputs.experiment }}-${{ github.ref }}",
    "group: ${{ github.workflow }}-${{ github.event.inputs.experiment }}-${{ github.event.inputs.ablate_gate || 'none' }}-${{ github.ref }}")
sub('  OUT_BASE:            "hypatiax/data/results"',
    "  OUT_BASE:            ${{ (github.event.inputs.ablate_gate != '' && github.event.inputs.ablate_gate != 'none' && github.event.inputs.ablate_gate != null) && format('hypatiax/data/results/option3_ablation/{0}', github.event.inputs.ablate_gate) || 'hypatiax/data/results' }}")
sub('  HYPATIAX_DISABLE_PROMPT_HINTS: "1"\n',
    '  HYPATIAX_DISABLE_PROMPT_HINTS: "1"\n  HDS_ABLATE_GATE:     "${{ github.event.inputs.ablate_gate || \'none\' }}"\n')
open(p, "w").write(s)
print("patched", p)
