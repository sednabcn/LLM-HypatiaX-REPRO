# ── 3b: Helper — seed control & case locator ─────────────────────────────────
def set_all_seeds(seed):
    random.seed(seed)
    np.random.seed(seed)
    if HYPATIA_AVAILABLE:
        torch.manual_seed(seed)
        try:
            torch.use_deterministic_algorithms(True)
        except Exception:
            pass


def _iter_protocol_cases(proto):
    """Normalize protocol cases across legacy and modern DeFi APIs.

    The older audit code expects `proto.get_cases()` and
    `proto.build_train_test_split(...)`. The current repository exposes
    `load_test_data()` / `get_all_domains()` instead. We translate the latter
    into the legacy shape that the notebook code expects.
    """
    domains = []
    if hasattr(proto, 'get_all_domains'):
        try:
            domains = list(proto.get_all_domains())
        except Exception:
            domains = []
    if not domains and hasattr(proto, 'domains'):
        domains = list(getattr(proto, 'domains').keys())

    records = []
    for domain in domains:
        try:
            rows = proto.load_test_data(domain, num_samples=200)
        except Exception:
            continue
        for idx, row in enumerate(rows):
            if not isinstance(row, tuple) or len(row) != 5:
                continue
            description, X, y, variables, metadata = row
            records.append({
                'name': description,
                'description': description,
                'domain': domain,
                'index': idx,
                'X': np.asarray(X),
                'y': np.asarray(y),
                'variables': list(variables),
                'metadata': dict(metadata or {}),
            })
    return records


def _split_case_data(X, y):
    """Portable train/test split used by the legacy notebook code."""
    X = np.asarray(X)
    y = np.asarray(y)
    if X.ndim == 1:
        X = X.reshape(-1, 1)

    if len(X) == 0:
        raise RuntimeError('Empty case data encountered while creating train/test split.')

    order = np.arange(len(X))
    vals = X[:, 0] if X.ndim > 1 and X.shape[1] > 0 else X.flatten()
    thresh = np.percentile(vals, 40)
    train_mask = vals <= thresh
    test_mask = vals > thresh

    if train_mask.sum() < 20 or test_mask.sum() < 20:
        train_mask = order < int(0.4 * len(order))
        test_mask = ~train_mask

    return X[train_mask], y[train_mask], X[test_mask], y[test_mask]


def find_portfolio_variance_case(proto):
    """Return (index, config) for Portfolio Variance in the DeFi protocol.

    Compatible with both the historical `get_cases()` API and the current
    `load_test_data()` protocol implementation used in this repository.
    """
    case_rows = _iter_protocol_cases(proto)
    if not case_rows:
        raise RuntimeError('Portfolio Variance case not found: protocol catalogue is empty.')

    for idx, cfg in enumerate(case_rows):
        name = (cfg.get('name') or cfg.get('description') or '').lower()
        if 'portfolio' in name or 'variance' in name:
            return idx, cfg

    # Fallback: if the current protocol names the case slightly differently,
    # prefer a variance/risk case rather than crashing on the stale API.
    for idx, cfg in enumerate(case_rows):
        name = (cfg.get('name') or cfg.get('description') or '').lower()
        if 'var' in name or 'risk' in name:
            return idx, cfg

    raise RuntimeError('Portfolio Variance case not found in the current DeFi protocol catalogue.')


print('Helper functions defined')

# ── 3c: Strategy A — single-case rerun at SEED=42 ────────────────────────────
strategy_a_result = None

if RERUN_STRATEGY == 'A' and HYPATIA_AVAILABLE and _run_case_full is None:
    print('Strategy A single-case rerun (3c) skipped — _run_case_full unavailable.')

elif RERUN_STRATEGY == 'A' and HYPATIA_AVAILABLE:
    print('Running Strategy A: Portfolio Variance at SEED=42 ...')
    set_all_seeds(BENCHMARK_SEED)
    proto = DeFiExperimentProtocol()
    try:
        pv_idx, pv_cfg = find_portfolio_variance_case(proto)
        print(f'Found: [{pv_idx}] "{pv_cfg["name"]}"')
        t0 = time.time()
        strategy_a_result = _run_case_full(proto, pv_idx, pv_cfg)
        print(f'\nCompleted in {time.time()-t0:.1f}s')
        print(json.dumps(strategy_a_result, indent=2, default=str))
    except Exception as e:
        print(f'Strategy A failed: {e}')

elif RERUN_STRATEGY == 'A' and not HYPATIA_AVAILABLE:
    print('Strategy A skipped — HypatiaX not available.')

# ── 3d: Strategy A — DeFi-protocol seed sweep (seeds 42, 99, 123, 777, 2024) ─
# Runs _hybrid_predict_and_eval for each seed under identical DeFi conditions.

if RERUN_STRATEGY == 'A' and HYPATIA_AVAILABLE:
    proto = DeFiExperimentProtocol()
    case_idx, case_cfg = find_portfolio_variance_case(proto)
    print(f'Case [{case_idx}]: "{case_cfg["name"]}"\n')

    for seed in SEEDS:
        print(f'-- Seed {seed} --')
        set_all_seeds(seed)
        X_train, y_train, X_test, y_test = _split_case_data(case_cfg['X'], case_cfg['y'])
        t0 = time.time()
        hybrid = _hybrid_predict_and_eval(
            case_cfg['description'], case_cfg.get('domain', 'DeFi'),
            X_train, y_train, X_test, y_test,
            case_cfg['variables'], case_cfg.get('metadata', {}))
        dt = time.time() - t0
        row = {'seed': seed, 'train_r2': hybrid['train_r2'],
               'far_r2': hybrid['test_r2'], 'decision': hybrid['decision'],
               'success': hybrid['test_r2'] > 0.99,
               'llm_train_r2': hybrid.get('llm_train_r2', float('nan')),
               'time_s': dt, 'llm_code': hybrid.get('llm_code')}
        defi_sweep_results.append(row)
        mark = 'OK' if row['success'] else 'FAIL'
        print(f'  {mark}  train_r2={row["train_r2"]:.4f}  '
              f'far_r2={row["far_r2"]:.4f}  time={dt:.1f}s')

    n_ok = sum(r['success'] for r in defi_sweep_results)
    print(f'\nDeFi-protocol success rate: {n_ok}/{len(SEEDS)} ({100*n_ok/len(SEEDS):.0f}%)')

    with open(SWEEP_JSON_DEFI, 'w') as f:
        json.dump({'case': case_cfg['name'], 'benchmark_version': 'v3c3', 'seeds_run': SEEDS,
                   'results': defi_sweep_results,
                   'summary': {'n_seeds': len(SEEDS), 'n_success': n_ok,
                               'success_rate': n_ok/len(SEEDS)}}, f, indent=2, default=str)
    print(f'DeFi-protocol sweep saved: {SWEEP_JSON_DEFI}')
