#!/usr/bin/env python3
"""Load result JSON contents into hypatiax_experiments.db.
  python3 ingest_json.py DB RESULTS_DIR [checksums.txt]
Steps: (1) attach sha256 + mark byte-identical duplicates (canonical copy = first non-saved/partial/rescued path),
(2) parse each CANONICAL json once, (3) fill typed tables per JSON family, (4) fill json_doc + json_item (generic leaves)."""
import sys, os, json, math, re, hashlib, sqlite3
db_path, root = sys.argv[1], sys.argv[2]
chk = sys.argv[3] if len(sys.argv)>3 else None
db = sqlite3.connect(db_path); c = db.cursor()

def num(x):
    if isinstance(x,bool): return int(x)
    if isinstance(x,(int,float)):
        return None if (isinstance(x,float) and math.isnan(x)) else float(x)
    return None
def b(x): return None if x is None else int(bool(x))
def integer(x):
    try: return None if x is None else int(x)
    except Exception: return None
def txt(x): return None if x is None else (x if isinstance(x,str) else json.dumps(x)[:4000])

# ---------- 1. checksums / duplicates ----------
if chk:
    for line in open(chk):
        parts=line.rstrip('\n').split(None,1)
        if len(parts)==2: c.execute('UPDATE result_file SET sha256=? WHERE rel_path=?',(parts[0],parts[1].strip().lstrip('./')))
for fid,rel in c.execute('SELECT file_id,rel_path FROM result_file').fetchall():
    fp=os.path.join(root,rel)
    if os.path.exists(fp):
        c.execute('UPDATE result_file SET in_zip=1 WHERE file_id=?',(fid,))
        if not chk or not c.execute('SELECT sha256 FROM result_file WHERE file_id=?',(fid,)).fetchone()[0]:
            c.execute('UPDATE result_file SET sha256=? WHERE file_id=?',(hashlib.sha256(open(fp,'rb').read()).hexdigest(),fid))
# verify zip bytes match recorded checksums
bad=[r for r in c.execute("SELECT rel_path FROM result_file WHERE in_zip=1 AND ext='json'").fetchall()
     if hashlib.sha256(open(os.path.join(root,r[0]),'rb').read()).hexdigest()!=c.execute('SELECT sha256 FROM result_file WHERE rel_path=?',r).fetchone()[0]]
print('checksum mismatches between zip and checksums.txt:',len(bad))
groups={}
for fid,sha,saved,part,resc,rel,inzip in c.execute("SELECT file_id,sha256,is_saved_copy,is_partial,is_rescued,rel_path,in_zip FROM result_file WHERE ext='json' AND sha256 IS NOT NULL").fetchall():
    groups.setdefault(sha,[]).append((saved,part,resc,0 if inzip else 1,rel,fid))
for sha,g in groups.items():
    g.sort(); canon=g[0][-1]
    for x in g[1:]: c.execute('UPDATE result_file SET duplicate_of=? WHERE file_id=?',(canon,x[-1]))
db.commit()

# ---------- helpers ----------
mcache={}
def method_id(n):
    if n not in mcache:
        c.execute('INSERT OR IGNORE INTO method(name) VALUES (?)',(n,)); mcache[n]=c.execute('SELECT method_id FROM method WHERE name=?',(n,)).fetchone()[0]
    return mcache[n]
ccache={}
def case_id(name,diff,ftype,intr):
    if name not in ccache:
        c.execute('INSERT OR IGNORE INTO defi_case(name,difficulty,formula_type,extrapolation_intractable) VALUES (?,?,?,?)',(name,diff,ftype,b(intr)))
        ccache[name]=c.execute('SELECT case_id FROM defi_case WHERE name=?',(name,)).fetchone()[0]
    return ccache[name]
SKIP_EXTRA={'y_pred_train','y_pred_test','llm_code','validation_r2'}
def extras(d,used):
    e={k:v for k,v in d.items() if k not in used and k not in ('y_pred_train','y_pred_test')}
    return json.dumps(e)[:3000] if e else None

# ---------- 2. family detectors / loaders ----------
def fam(d):
    if isinstance(d,list):
        if not d: return 'empty_list'
        x=d[0]
        if isinstance(x,dict):
            if 'equation_id' in x and 'results' in x: return 'defi_cases_list'
            if 'test_case' in x and 'results' in x: return 'defi_cases_list'
            if {'test','domain','method','r2'}<=set(x): return 'benchmark_rows'
            if 'method' in x and 'decision' in x: return 'hybrid_all_domains'
        return 'other_list'
    if not isinstance(d,dict): return 'scalar'
    k=set(d)
    if 'cases' in k and 'benchmark' in k: return 'defi_cases_dict'
    if 'tests' in k and 'methods' in k: return 'protocol_run'
    if {'config','results','summary'}<=k: return 'nguyen'
    if k=={'completed','run_id_map'}: return 'checkpoint_stub'
    if 'fixc3_gate' in k: return 'fixc3_gate'
    if 'per_noise' in k: return 'noise_sweep'
    if 'per_n' in k: return 'sample_complexity'
    if 'core15_instability' in k: return 'instability'
    if {'pysr_only','hypatia'}<=k and isinstance(d['pysr_only'],list): return 'portfolio_seed_sweep'
    if {'case','results','seeds_run'}<=k: return 'portfolio_defi_seed'
    if 'contradiction_summary' in k: return 'contradiction_audit'
    if d and all(re.fullmatch(r'\d+',x) for x in k):
        v=next(iter(d.values()))
        if isinstance(v,dict) and 'pysr_only' in v and 'name' in v and 'wall_secs' in v['pysr_only']: return 'wall_clock'
        if isinstance(v,dict) and 'name' in v and 'domain' in v: return 'ablation'
        return 'numeric_keyed'
    return 'other_dict'

def load_defi(fid,d,rel):
    cases = d if isinstance(d,list) else d['cases']
    m=re.search(r'seed(\d+)',rel); fseed=int(m.group(1)) if m else None
    n=0
    for cs in cases:
        name=cs.get('equation_id') or cs.get('test_case'); cid=case_id(name,cs.get('difficulty'),cs.get('formula_type'),cs.get('extrapolation_intractable'))
        seed=cs.get('seed',fseed)
        res=cs.get('results')
        if not isinstance(res,dict): continue
        for s,r in res.items():
            if not isinstance(r,dict): continue
            used={'train_r2','test_r2','success','timed_out','time_s','extrapolation_gap','stability_score','decision'}
            c.execute('INSERT INTO defi_case_result(file_id,case_id,seed,system,train_r2,test_r2,success,timed_out,time_s,extrapolation_gap,stability_score,decision,extra_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
              (fid,cid,seed,s,num(r.get('train_r2')),num(r.get('test_r2')),b(r.get('success')),b(r.get('timed_out')),num(r.get('time_s')),
               num(r.get('extrapolation_gap')),num(r.get('stability_score')),txt(r.get('decision')),extras(r,used))); n+=1
    return n

def load_protocol(fid,d,rel):
    p=d.get('protocol') or {}
    c.execute('INSERT INTO protocol_run VALUES (?,?,?,?,?,?,?,?,?,?)',(fid,d.get('timestamp'),d.get('script'),p.get('mode'),num(p.get('noise_level')),
      num(p.get('threshold')),integer(d.get('total_tests')),len(d.get('methods') or []),b(d.get('completed')),b(d.get('had_timeouts'))))
    n=0
    for t in d['tests']:
        cmp_=t.get('comparison') or {}
        c.execute('INSERT INTO protocol_test(file_id,description,domain,winner) VALUES (?,?,?,?)',(fid,t.get('description'),t.get('domain'),txt(t.get('winner') or cmp_.get('winner'))))
        tid=c.lastrowid; ranks=cmp_.get('rankings') or {}
        for m,r in (t.get('results') or {}).items():
            if not isinstance(r,dict): continue
            c.execute('INSERT INTO protocol_result(test_id,file_id,method,success,r2,rmse,time_s,formula,formula_hash,error,rank) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
              (tid,fid,m,b(r.get('success')),num(r.get('r2')),num(r.get('rmse')),num(r.get('time')),txt(r.get('formula')),r.get('formula_hash'),txt(r.get('error')),integer(ranks.get(m)))); n+=1
    return n

def load_nguyen(fid,d,rel):
    cf,sm=d['config'],d['summary']
    c.execute('INSERT INTO nguyen_run VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(fid,cf.get('seed'),num(cf.get('temperature')),cf.get('n_tasks'),cf.get('niterations'),
      cf.get('populations'),cf.get('timeout'),b(cf.get('use_llm')),cf.get('schema_version'),cf.get('n_candidates'),num(cf.get('llm_min_r2')),cf.get('llm_k_runs'),
      sm.get('h_recovered'),sm.get('p_recovered'),sm.get('n_total'),num(sm.get('h_rate')),num(sm.get('p_rate')),sm.get('n_completed'),b(sm.get('complete'))))
    n=0
    for sysname,lst in d['results'].items():
        for e in lst:
            ev=e.get('evaluation') or {}; md=e.get('metadata') or {}
            c.execute('INSERT INTO nguyen_result(file_id,system,equation_name,expression,r2,r2_train,r2_extrap,elapsed_s,trajectory_len,llm_guesses_used,llm_candidates_total,llm_candidates_parsed,llm_gate_failed,llm_error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
              (fid,sysname,md.get('equation_name'),txt(e.get('expression')),num(ev.get('r2')),num(ev.get('r2_train')),num(ev.get('r2_extrap')),num(e.get('elapsed')),
               len(e.get('trajectory') or []),e.get('llm_guesses_used'),e.get('llm_candidates_total'),e.get('llm_candidates_parsed'),b(e.get('llm_gate_failed')),txt(e.get('llm_error')))); n+=1
            for i,t in enumerate(e.get('trajectory') or []):
                c.execute('INSERT INTO nguyen_trajectory(file_id,system,equation_name,step,iteration,label,best_loss,best_complexity,best_score,elapsed_seconds,best_expression) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                  (fid,sysname,md.get('equation_name'),i,integer(t.get('iteration')),txt(t.get('label')),num(t.get('best_loss')),integer(t.get('best_complexity')),num(t.get('best_score')),num(t.get('elapsed_seconds')),txt(t.get('best_expression'))[:500] if t.get('best_expression') else None))
    return n

def load_fixc3(fid,d,rel):
    c.execute('INSERT INTO fixc3_gate VALUES (?,?,?,?,?,?,?,?,?)',(fid,d.get('fixc3_gate'),d.get('description'),d.get('split_protocol'),integer(d.get('n_pass')),
      integer(d.get('n_total')),num(d.get('solve_rate')),d.get('paper_claim'),len(d.get('source_files') or []))); return 1

def load_benchmark_rows(fid,d,rel):
    for r in d: c.execute('INSERT INTO benchmark_row(file_id,test,domain,method,formula,r2,rmse,runtime_s,success) VALUES (?,?,?,?,?,?,?,?,?)',
        (fid,r.get('test'),r.get('domain'),r.get('method'),txt(r.get('formula')),num(r.get('r2')),num(r.get('rmse')),num(r.get('runtime')),b(r.get('success'))))
    return len(d)

def load_sweep(fid,d,rel):
    key,sw='per_noise','noise' if 'per_noise' in d else 'per_n'
    key='per_noise' if 'per_noise' in d else 'per_n'; sw='noise' if key=='per_noise' else 'sample_size'
    n=0
    for lvl,blk in d[key].items():
        for m,s in (blk.get('method_summary') or {}).items():
            c.execute('INSERT INTO sweep_cell(file_id,sweep,level,method,median_r2,mean_r2,std_r2,recovery_rate,n_success,n_total,threshold_used,n_catastrophic,mean_time_s,median_time_s) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
              (fid,sw,num(float(lvl)),m,num(s.get('median_r2')),num(s.get('mean_r2')),num(s.get('std_r2')),num(s.get('recovery_rate')),integer(s.get('n_success')),integer(s.get('n_total')),
               num(s.get('threshold_used')),integer(s.get('n_catastrophic')),num(s.get('mean_time_s')),num(s.get('median_time_s')))); n+=1
    return n

def load_ablation(fid,d,rel):
    n=0
    for idx,rec in d.items():
        for cond,r in rec.items():
            if isinstance(r,dict) and 'condition' in r:
                c.execute('INSERT INTO ablation_result(file_id,idx,equation,domain,condition,success,timed_out,excluded_from_timing,train_r2,train_rmse,extrap_r2_near,extrap_r2_medium,extrap_r2_far,extrap_rmse_near,extrap_rmse_medium,extrap_rmse_far,sr_time_s,llm_time_s,total_time_s,best_expression,complexity,llm_expression,llm_confidence) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (fid,int(idx),rec.get('name'),rec.get('domain'),r['condition'],b(r.get('success')),b(r.get('timed_out')),b(r.get('excluded_from_timing')),num(r.get('train_r2')),num(r.get('train_rmse')),
                   num(r.get('extrap_r2_near')),num(r.get('extrap_r2_medium')),num(r.get('extrap_r2_far')),num(r.get('extrap_rmse_near')),num(r.get('extrap_rmse_medium')),num(r.get('extrap_rmse_far')),
                   num(r.get('sr_time_s')),num(r.get('llm_time_s')),num(r.get('total_time_s')),txt(r.get('best_expression')),integer(r.get('complexity')),txt(r.get('llm_expression')),num(r.get('llm_confidence')))); n+=1
    return n

def load_wall(fid,d,rel):
    n=0
    for idx,rec in d.items():
        for cond in ('pysr_only','hypatia'):
            r=rec.get(cond)
            if isinstance(r,dict):
                c.execute('INSERT INTO wall_clock_flag(file_id,idx,equation,condition,timed_out,excluded_from_timing,wall_secs) VALUES (?,?,?,?,?,?,?)',
                  (fid,int(idx),rec.get('name'),cond,b(r.get('timed_out')),b(r.get('excluded_from_timing')),num(r.get('wall_secs')))); n+=1
    return n

def load_instab(fid,d,rel):
    for r in d['core15_instability']:
        c.execute('INSERT INTO instability_row(file_id,equation,domain,extrap_r2_near,extrap_r2_far,instability_index) VALUES (?,?,?,?,?,?)',
          (fid,r.get('equation'),r.get('domain'),num(r.get('extrap_r2_near')),num(r.get('extrap_r2_far')),num(r.get('instability_index'))))
    return len(d['core15_instability'])

def load_pv(fid,d,rel):
    n=0
    for cond in ('pysr_only','hypatia'):
        for r in d.get(cond,[]):
            c.execute('INSERT INTO portfolio_seed_result(file_id,condition,seed,train_r2,near_r2,medium_r2,far_r2,time_s,success,timed_out,decision,expression) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
              (fid,cond,r.get('seed'),num(r.get('train_r2')),num(r.get('near_r2')),num(r.get('medium_r2')),num(r.get('far_r2')),num(r.get('time_s')),b(r.get('success')),b(r.get('timed_out')),txt(r.get('decision')),txt(r.get('expr')))); n+=1
    return n
def load_pv_defi(fid,d,rel):
    for r in d['results']:
        c.execute('INSERT INTO portfolio_seed_result(file_id,condition,seed,train_r2,near_r2,medium_r2,far_r2,time_s,success,timed_out,decision,expression) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
          (fid,'hypatia_'+str(d.get('benchmark_version')),r.get('seed'),num(r.get('train_r2')),None,None,num(r.get('far_r2')),num(r.get('time_s')),b(r.get('success')),None,txt(r.get('decision')),txt(r.get('llm_code'))))
    return len(d['results'])
def load_audit(fid,d,rel):
    s=d['contradiction_summary']
    c.execute('INSERT INTO audit_finding(file_id,claim,actual_seed42,actual_seed99,conclusion) VALUES (?,?,?,?,?)',(fid,s.get('claim_in_paper'),s.get('actual_result_at_seed_42'),s.get('actual_result_at_seed_99'),s.get('conclusion'))); return 1

LOADERS={'defi_cases_list':load_defi,'defi_cases_dict':load_defi,'protocol_run':load_protocol,'nguyen':load_nguyen,'fixc3_gate':load_fixc3,
 'benchmark_rows':load_benchmark_rows,'noise_sweep':load_sweep,'sample_complexity':load_sweep,'ablation':load_ablation,'wall_clock':load_wall,
 'instability':load_instab,'portfolio_seed_sweep':load_pv,'portfolio_defi_seed':load_pv_defi,'contradiction_audit':load_audit}

# ---------- 3. generic EAV (arrays of scalars summarised) ----------
def leaves(o,path='$',parent=None,key=None,depth=0):
    if isinstance(o,dict):
        for k,v in o.items(): yield from leaves(v,f'{path}.{k}',path,k,depth+1)
    elif isinstance(o,list):
        if key in ('trajectory','llm_gate_audit') and len(o)>0:
            yield path,parent,key,depth,f'list[{len(o)}] (see typed table)'
        elif len(o)>20 and all(not isinstance(x,(dict,list)) for x in o):
            nums=[x for x in o if isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)]
            s=f'array[{len(o)}]'+(f' min={min(nums):.6g} max={max(nums):.6g}' if nums else '')
            yield path,parent,key,depth,s
        else:
            for i,v in enumerate(o): yield from leaves(v,f'{path}[{i}]',path,key,depth+1)
    else: yield path,parent,key,depth,o

stats={}; errs=[]
canon=c.execute("SELECT file_id,rel_path FROM result_file WHERE ext='json' AND duplicate_of IS NULL AND in_zip=1 ORDER BY file_id").fetchall()
for fid,rel in canon:
    for t in ('json_item','json_doc','defi_case_result'): c.execute(f'DELETE FROM {t} WHERE file_id=?',(fid,))
    raw=open(os.path.join(root,rel),'rb').read()
    try: d=json.loads(raw)
    except Exception as e:
        c.execute('INSERT INTO json_doc VALUES (?,?,?,?,?,?)',(fid,hashlib.sha256(raw).hexdigest(),len(raw),None,None,'not JSON: '+str(e)[:80]))
        c.execute('UPDATE result_file SET family=? WHERE file_id=?',('text_saved_as_json',fid)); stats['text_saved_as_json']=stats.get('text_saved_as_json',0)+1; continue
    f=fam(d)
    c.execute('UPDATE result_file SET family=? WHERE file_id=?',(f,fid))
    c.execute('INSERT INTO json_doc VALUES (?,?,?,?,?,?)',(fid,hashlib.sha256(raw).hexdigest(),len(raw),type(d).__name__,len(d) if isinstance(d,(dict,list)) else None,None))
    if f in LOADERS:
        try: stats[f]=stats.get(f,0)+LOADERS[f](fid,d,rel)
        except Exception as e: errs.append((rel,f,repr(e)[:120]))
    rows=[]
    for p,par,k,dp,v in leaves(d):
        vt='null' if v is None else 'bool' if isinstance(v,bool) else 'num' if isinstance(v,(int,float)) else 'text'
        vn=float(v) if vt=='num' and math.isfinite(v) else None
        rows.append((fid,p,par,k,dp,vt,vn,(str(v)[:500] if vt=='text' or (vt=='num' and vn is None) else None),int(v) if vt=='bool' else None))
    c.executemany('INSERT INTO json_item(file_id,json_path,parent_path,key,depth,vtype,v_num,v_text,v_bool) VALUES (?,?,?,?,?,?,?,?,?)',rows)
    c.execute('UPDATE result_file SET content_loaded=1 WHERE file_id=?',(fid,))
# duplicates inherit family + loaded flag
c.execute("UPDATE result_file SET family=(SELECT o.family FROM result_file o WHERE o.file_id=result_file.duplicate_of), content_loaded=2 WHERE duplicate_of IS NOT NULL")
db.commit()
print('canonical parsed:',len(canon)); print('typed rows:',stats); print('loader errors:',errs)
