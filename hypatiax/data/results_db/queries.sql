-- Experiment overview
SELECT * FROM v_experiment_summary WHERE n_files>0;
-- Hybrid vs baselines on the DeFi benchmark, per experiment/version/seed-set
SELECT * FROM v_defi_success ORDER BY experiment_id, benchmark_version;
-- Feynman protocol runs: success / R2 / time per method
SELECT * FROM v_protocol_method_summary ORDER BY experiment_id, method;
-- Nguyen-12 recovery per seed/temperature (HypatiaX vs PySR), canonical + duplicate files flagged
SELECT * FROM v_nguyen_summary WHERE is_partial=0 ORDER BY experiment_id, seed, temperature;
-- Per-equation Nguyen-12 results for one run
SELECT system, equation_name, r2, r2_extrap, elapsed_s FROM nguyen_result
WHERE file_id=(SELECT file_id FROM result_file WHERE rel_path='extrapolation/exp3_nguyen12_seed42.json');
-- Core-15 ablation: PySR-only vs HypatiaX far-region R2
SELECT equation, condition, extrap_r2_near, extrap_r2_far, total_time_s FROM ablation_result a JOIN result_file f USING(file_id)
WHERE f.rel_path='ablation/exp1_ablation/exp1_ablation_results_shard0.json' OR f.rel_path LIKE '%exp1_ablation_checkpoint_shard%' GROUP BY equation, condition;
-- Noise sweep / sample complexity
SELECT sweep, level, method, recovery_rate, median_r2, n_catastrophic FROM sweep_cell ORDER BY sweep, method, level;
-- Which files are byte-identical copies of which
SELECT d.rel_path AS duplicate, c.rel_path AS canonical FROM result_file d JOIN result_file c ON c.file_id=d.duplicate_of;
-- Every raw leaf value in a file (generic fallback for formats without a typed table)
SELECT json_path, vtype, v_num, v_text FROM json_item WHERE file_id=(SELECT COALESCE(duplicate_of,file_id) FROM result_file WHERE rel_path='fixc3_baseline.json');  -- duplicates point to the parsed copy
