# HypatiaX experiments database (hypatiax_experiments.db, SQLite)

Built from: tree_results.txt, run_all.sh, checksums.txt, results.zip (385 of 410 JSON; the 25 in
extrapolation_sparse_seed_off were left out of the zip but are byte-identical to files in extrapolation/, confirmed by checksum).

Rebuild:   python3 build_db.py tree_results.txt run_all.sh hypatiax_experiments.db
Load JSON: python3 ingest_json.py hypatiax_experiments.db <path>/results checksums.txt

## Layers
Pipeline:   experiment (40), script, experiment_script, experiment_param      <- run_all.sh
Inventory:  result_file (432 files; sha256, duplicate_of, family, seed/shard/temp/timestamp parsed from names)
Contents:   json_doc (258 unique JSON), json_item (every leaf value; big arrays summarised)
Typed:      defi_case, defi_case_result | protocol_run, protocol_test, protocol_result | nguyen_run, nguyen_result,
            nguyen_trajectory | ablation_result, wall_clock_flag, instability_row | sweep_cell | portfolio_seed_result |
            fixc3_gate | benchmark_row | audit_finding
Views:      v_experiment_summary, v_defi_success, v_protocol_method_summary, v_nguyen_summary, v_duplicate_groups,
            v_rescued_vs_original, v_seed_coverage, v_unmapped_files

result_file.content_loaded: 1 = parsed, 2 = identical bytes to a parsed file (see duplicate_of), 0 = not parsed.
Files with family 'other_dict'/'hybrid_all_domains'/'checkpoint_stub' have no typed table; query json_item.
6 "*.json" files in exp1_ablation are logs/CSV saved with a .json name; they are flagged text_saved_as_json, not parsed.
CSV files are inventoried but not loaded.
