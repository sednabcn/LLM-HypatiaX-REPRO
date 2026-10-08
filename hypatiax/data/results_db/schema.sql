PRAGMA foreign_keys=ON;

-- ===== Pipeline layer (from run_all.sh) =====
CREATE TABLE experiment(
  experiment_id TEXT PRIMARY KEY,          -- run_all.sh step name
  step_order    INTEGER,                   -- position in _STEP_ORDER
  description   TEXT,
  paper_refs    TEXT,                      -- Tab/Fig/§ mentioned in the step description
  produces_results INTEGER NOT NULL,       -- 1 = writes files under results/
  notes         TEXT);
CREATE TABLE script(script_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE experiment_script(
  experiment_id TEXT REFERENCES experiment, script_id INTEGER REFERENCES script,
  PRIMARY KEY(experiment_id,script_id));
CREATE TABLE experiment_param(               -- CLI flags / env defaults found in run_all.sh
  experiment_id TEXT, param TEXT, value TEXT, PRIMARY KEY(experiment_id,param,value));

-- ===== File inventory layer (from tree_results.txt; metadata parsed from path/filename) =====
CREATE TABLE result_file(
  file_id INTEGER PRIMARY KEY,
  rel_path TEXT UNIQUE NOT NULL, dir_path TEXT, file_name TEXT, ext TEXT,
  experiment_id TEXT REFERENCES experiment,
  mapping_basis TEXT,                      -- how the file was tied to an experiment
  file_kind TEXT,                          -- checkpoint, protocol_run, benchmark_results, rescued_shard, ...
  shard INTEGER, n_shards INTEGER, seed INTEGER, temperature REAL, run_no INTEGER,
  run_timestamp TEXT,                      -- parsed from YYYYMMDD_HHMMSS in the name
  is_rescued INTEGER DEFAULT 0, rescued_epoch INTEGER, rescued_base_name TEXT,
  is_partial INTEGER DEFAULT 0, is_saved_copy INTEGER DEFAULT 0,
  feynman_domain TEXT, benchmark_version TEXT, split_protocol TEXT, phase TEXT,
  content_loaded INTEGER DEFAULT 0);        -- set to 1 by ingest_json.py
CREATE INDEX ix_rf_exp ON result_file(experiment_id);
CREATE INDEX ix_rf_kind ON result_file(file_kind);
CREATE INDEX ix_rf_seed ON result_file(seed);

-- ===== Content layer (filled by ingest_json.py from the real JSON files) =====
CREATE TABLE json_doc(                       -- one row per ingested JSON
  file_id INTEGER PRIMARY KEY REFERENCES result_file, sha256 TEXT, size_bytes INTEGER,
  top_level_type TEXT, n_top_keys INTEGER, parse_error TEXT);
CREATE TABLE json_item(                      -- every leaf value: schema-agnostic EAV
  item_id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file,
  json_path TEXT NOT NULL,                   -- e.g. $.results[3].r2
  parent_path TEXT, key TEXT, depth INTEGER,
  vtype TEXT, v_num REAL, v_text TEXT, v_bool INTEGER);
CREATE INDEX ix_ji_file ON json_item(file_id);
CREATE INDEX ix_ji_key  ON json_item(key);

-- ===== Views =====
CREATE VIEW v_experiment_summary AS
SELECT e.experiment_id, e.step_order, e.description, e.paper_refs,
       COUNT(f.file_id) n_files,
       SUM(f.ext='json') n_json,
       SUM(f.file_kind IN('benchmark_results','protocol_run','nguyen12_result','hybrid_result','seed_sweep','summary')) n_result_files,
       SUM(f.is_rescued) n_rescued, SUM(f.is_partial) n_partial,
       COUNT(DISTINCT f.seed) n_seeds, MIN(f.run_timestamp) first_ts, MAX(f.run_timestamp) last_ts,
       SUM(f.content_loaded) n_loaded
FROM experiment e LEFT JOIN result_file f USING(experiment_id)
GROUP BY e.experiment_id ORDER BY e.step_order;
CREATE VIEW v_seed_coverage AS
SELECT experiment_id, seed, COUNT(*) n_files, GROUP_CONCAT(DISTINCT file_kind) kinds
FROM result_file WHERE seed IS NOT NULL GROUP BY experiment_id, seed;
CREATE VIEW v_rescued_vs_original AS      -- each rescued shard next to its base file
SELECT r.file_id rescued_id, r.rel_path rescued_path, r.shard, r.rescued_epoch,
       datetime(r.rescued_epoch,'unixepoch') rescued_at, o.file_id original_id, o.rel_path original_path
FROM result_file r LEFT JOIN result_file o
  ON o.dir_path=r.dir_path AND o.is_rescued=0 AND
     (o.file_name=r.rescued_base_name || '.json' OR o.file_name=r.rescued_base_name)
WHERE r.is_rescued=1;
CREATE VIEW v_unmapped_files AS SELECT * FROM result_file WHERE experiment_id IS NULL;

-- ===== Typed result layer (v2) =====
ALTER TABLE result_file ADD COLUMN sha256 TEXT;
ALTER TABLE result_file ADD COLUMN duplicate_of INTEGER REFERENCES result_file(file_id);  -- canonical file with identical bytes
ALTER TABLE result_file ADD COLUMN in_zip INTEGER DEFAULT 0;
ALTER TABLE result_file ADD COLUMN family TEXT;                                           -- JSON shape family
CREATE INDEX ix_rf_sha ON result_file(sha256);

CREATE TABLE defi_case(case_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, difficulty TEXT, formula_type TEXT, extrapolation_intractable INTEGER);
CREATE TABLE defi_case_result(                 -- DeFi benchmark v3/v3c/v4/pca: one row per file x case x seed x system
  id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file, case_id INTEGER REFERENCES defi_case,
  seed INTEGER, system TEXT, train_r2 REAL, test_r2 REAL, success INTEGER, timed_out INTEGER, time_s REAL,
  extrapolation_gap REAL, stability_score REAL, decision TEXT, extra_json TEXT);
CREATE INDEX ix_dcr ON defi_case_result(file_id, case_id);
CREATE TABLE protocol_run(                     -- protocol_core_* and pca4060 checkpoint files
  file_id INTEGER PRIMARY KEY REFERENCES result_file, run_timestamp TEXT, script TEXT, mode TEXT, noise_level REAL,
  threshold REAL, total_tests INTEGER, n_methods INTEGER, completed INTEGER, had_timeouts INTEGER);
CREATE TABLE protocol_test(test_id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file, description TEXT, domain TEXT, winner TEXT);
CREATE TABLE protocol_result(                  -- one row per file x test x method
  id INTEGER PRIMARY KEY, test_id INTEGER REFERENCES protocol_test, file_id INTEGER REFERENCES result_file,
  method TEXT, success INTEGER, r2 REAL, rmse REAL, time_s REAL, formula TEXT, formula_hash TEXT, error TEXT, rank INTEGER);
CREATE INDEX ix_pr ON protocol_result(file_id, method);
CREATE TABLE nguyen_run(                       -- exp3 config + summary
  file_id INTEGER PRIMARY KEY REFERENCES result_file, seed INTEGER, temperature REAL, n_tasks INTEGER, niterations INTEGER,
  populations INTEGER, timeout INTEGER, use_llm INTEGER, schema_version TEXT, n_candidates INTEGER, llm_min_r2 REAL,
  llm_k_runs INTEGER, h_recovered INTEGER, p_recovered INTEGER, n_total INTEGER, h_rate REAL, p_rate REAL, n_completed INTEGER, complete INTEGER);
CREATE TABLE nguyen_result(
  id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file, system TEXT, equation_name TEXT, expression TEXT,
  r2 REAL, r2_train REAL, r2_extrap REAL, elapsed_s REAL, trajectory_len INTEGER, llm_guesses_used INTEGER,
  llm_candidates_total INTEGER, llm_candidates_parsed INTEGER, llm_gate_failed INTEGER, llm_error TEXT);
CREATE TABLE fixc3_gate(file_id INTEGER PRIMARY KEY REFERENCES result_file, gate TEXT, description TEXT, split_protocol TEXT,
  n_pass INTEGER, n_total INTEGER, solve_rate REAL, paper_claim TEXT, n_source_files INTEGER);
CREATE TABLE benchmark_row(id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file, test TEXT, domain TEXT, method TEXT,
  formula TEXT, r2 REAL, rmse REAL, runtime_s REAL, success INTEGER);
CREATE TABLE sweep_cell(                       -- noise sweep (level=noise) and sample complexity (level=n)
  id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file, sweep TEXT, level REAL, method TEXT,
  median_r2 REAL, mean_r2 REAL, std_r2 REAL, recovery_rate REAL, n_success INTEGER, n_total INTEGER, threshold_used REAL,
  n_catastrophic INTEGER, mean_time_s REAL, median_time_s REAL);
CREATE TABLE ablation_result(                  -- exp1_ablation_* and exp1_five_*: one row per file x equation x condition
  id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file, idx INTEGER, equation TEXT, domain TEXT, condition TEXT,
  success INTEGER, timed_out INTEGER, excluded_from_timing INTEGER, train_r2 REAL, train_rmse REAL,
  extrap_r2_near REAL, extrap_r2_medium REAL, extrap_r2_far REAL, extrap_rmse_near REAL, extrap_rmse_medium REAL, extrap_rmse_far REAL,
  sr_time_s REAL, llm_time_s REAL, total_time_s REAL, best_expression TEXT, complexity INTEGER, llm_expression TEXT, llm_confidence REAL);
CREATE TABLE wall_clock_flag(id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file, idx INTEGER, equation TEXT, condition TEXT,
  timed_out INTEGER, excluded_from_timing INTEGER, wall_secs REAL);
CREATE TABLE instability_row(id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file, equation TEXT, domain TEXT,
  extrap_r2_near REAL, extrap_r2_far REAL, instability_index REAL);
CREATE TABLE portfolio_seed_result(id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file, condition TEXT, seed INTEGER,
  train_r2 REAL, near_r2 REAL, medium_r2 REAL, far_r2 REAL, time_s REAL, success INTEGER, timed_out INTEGER, decision TEXT, expression TEXT);
CREATE TABLE audit_finding(id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file, claim TEXT, actual_seed42 TEXT, actual_seed99 TEXT, conclusion TEXT);

CREATE VIEW v_duplicate_groups AS
SELECT sha256, COUNT(*) n_files, MIN(file_id) first_id, GROUP_CONCAT(rel_path,' | ') paths FROM result_file
WHERE ext='json' AND sha256 IS NOT NULL GROUP BY sha256 HAVING COUNT(*)>1;
CREATE VIEW v_defi_pivot AS
SELECT f.experiment_id, f.benchmark_version, f.split_protocol, r.seed, c.name case_name, c.difficulty,
  MAX(CASE WHEN r.system='pure_llm' THEN r.test_r2 END) llm_test_r2,
  MAX(CASE WHEN r.system='neural_network' THEN r.test_r2 END) nn_test_r2,
  MAX(CASE WHEN r.system='hybrid' THEN r.test_r2 END) hybrid_test_r2,
  MAX(CASE WHEN r.system='hybrid' THEN r.success END) hybrid_success, r.file_id
FROM defi_case_result r JOIN defi_case c USING(case_id) JOIN result_file f USING(file_id)
GROUP BY r.file_id, r.seed, c.case_id;

CREATE TABLE nguyen_trajectory(                -- PySR search trajectory per equation (from exp3 'trajectory' lists)
  id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES result_file, system TEXT, equation_name TEXT, step INTEGER,
  iteration INTEGER, label TEXT, best_loss REAL, best_complexity INTEGER, best_score REAL, elapsed_seconds REAL, best_expression TEXT);
CREATE INDEX ix_nt ON nguyen_trajectory(file_id, equation_name);

CREATE VIEW v_nguyen_summary AS
SELECT f.experiment_id, f.rel_path, f.duplicate_of IS NOT NULL is_duplicate, n.seed, n.temperature, n.n_total,
       n.h_recovered hypatiax_recovered, n.p_recovered pysr_recovered, n.h_rate, n.p_rate, n.complete, f.is_partial
FROM nguyen_run n JOIN result_file f USING(file_id);
CREATE VIEW v_protocol_method_summary AS     -- canonical files only
SELECT f.experiment_id, p.mode, p.noise_level, r.method, COUNT(*) n_results, SUM(r.success) n_success,
       ROUND(AVG(r.success),3) success_rate, ROUND(AVG(r.r2),4) mean_r2, ROUND(AVG(r.time_s),1) mean_time_s
FROM protocol_result r JOIN protocol_run p USING(file_id) JOIN result_file f USING(file_id)
WHERE f.duplicate_of IS NULL GROUP BY f.experiment_id, p.mode, p.noise_level, r.method;
CREATE VIEW v_defi_success AS               -- canonical files only
SELECT f.experiment_id, f.benchmark_version, f.split_protocol, r.system, COUNT(*) n, SUM(r.success) n_success,
       ROUND(AVG(r.success),3) success_rate, COUNT(DISTINCT r.seed) n_seeds
FROM defi_case_result r JOIN result_file f USING(file_id) WHERE f.duplicate_of IS NULL
GROUP BY f.experiment_id, f.benchmark_version, f.split_protocol, r.system;
