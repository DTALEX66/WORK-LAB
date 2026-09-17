"""WORK-LAB Observer - Token/Cost estimator (ESTIMATED quality).

Reads real DSH session activity (assistant messages / reasoning chunks per
project) and writes estimated usage_samples into canonical.sqlite.
ESTIMATED by design: DSH/Hermes do not expose exact token counters; the
estimate is derived from real call counts x industry-average tokens per call,
priced at DeepSeek reasoner rates. quality=ESTIMATED, never presented as exact.
"""
import json, os, sqlite3, zstandard
from datetime import datetime, timezone

BASE = r'D:\All projects\WORK-LAB\.hermes\task-runtime\deepseek-harness\dsh-home\sessions'
DB = r'D:\All projects\WORK-LAB\.hermes\task-runtime\canonical.sqlite'

# Estimate model (tokens per LLM call, industry averages for coding agents)
TOKENS_PER_CALL_INPUT = 4200      # context + prompt
TOKENS_PER_CALL_OUTPUT = 1400     # assistant output
TOKENS_PER_CALL_REASONING = 2400  # reasoning tokens (deepseek reasoner)
TOOL_TOKENS_PER_CALL = 900        # tool call serialization

# DeepSeek pricing (USD per 1M tokens) - reasoner
PRICE_INPUT = 0.55
PRICE_OUTPUT = 2.19

dctx = zstandard.ZstdDecompressor()

def decode(path):
    try:
        with open(path, 'rb') as fh:
            reader = dctx.stream_reader(fh)
            chunks = []
            while True:
                c = reader.read(65536)
                if not c: break
                chunks.append(c)
        return b''.join(chunks).decode('utf-8', errors='replace').splitlines()
    except Exception:
        return []

def activity(proj_dir):
    pdir = os.path.join(BASE, proj_dir)
    counts = {}
    if not os.path.isdir(pdir): return counts
    for root, dirs, files in os.walk(pdir):
        for fn in files:
            if not fn.endswith('.zstd'): continue
            for line in decode(os.path.join(root, fn)):
                try:
                    rec = json.loads(line)
                    t = rec.get('type') or 'unknown'
                    counts[t] = counts.get(t, 0) + 1
                except Exception:
                    pass
    return counts

PROJECT_MAP = {
    '--D-All~0020projects-WORK-LAB--': 'work-lab',
    '--D-All~0020projects-DESIGN-LAB--': 'design-lab',
    '--D-All~0020projects-ArcheAxis-Knowledge-OS--': 'archeaxis-knowledge-os',
}

rows = []
for proj_dir, pid in PROJECT_MAP.items():
    c = activity(proj_dir)
    calls = c.get('assistant/message', 0)
    if calls == 0:
        continue
    inp = calls * TOKENS_PER_CALL_INPUT
    out = calls * TOKENS_PER_CALL_OUTPUT
    rea = calls * TOKENS_PER_CALL_REASONING
    tool = c.get('tool/call', 0) * TOOL_TOKENS_PER_CALL
    total = inp + out + rea + tool
    cost = (inp / 1e6 * PRICE_INPUT) + ((out + rea + tool) / 1e6 * PRICE_OUTPUT)
    rows.append((pid, calls, inp, out, rea, tool, total, round(cost, 4)))

print('project | calls | input | output | reasoning | tool | total | cost(USD)')
for r in rows:
    print(f'{r[0]} | {r[1]} | {r[2]:,} | {r[3]:,} | {r[4]:,} | {r[5]:,} | {r[6]:,} | {r[7]}')

# upsert into usage_samples (ESTIMATED quality)
conn = sqlite3.connect(DB)
cur = conn.cursor()
now = datetime.now(timezone.utc).isoformat()
for pid, calls, inp, out, rea, tool, total, cost in rows:
    sid = f'estimate-{pid}'
    cur.execute("""
        INSERT INTO usage_samples
        (sample_id, project_id, provider, model, lane, observed_at, window_start, window_end,
         input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens,
         tool_tokens, subagent_tokens, total_tokens, billing_type, cost_estimate, cost_reconciled,
         quality, source_ref)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(sample_id) DO UPDATE SET
          input_tokens=excluded.input_tokens, output_tokens=excluded.output_tokens,
          reasoning_tokens=excluded.reasoning_tokens, tool_tokens=excluded.tool_tokens,
          total_tokens=excluded.total_tokens, cost_estimate=excluded.cost_estimate,
          observed_at=excluded.observed_at
    """, (sid, pid, 'deepseek', 'deepseek-reasoner', 'estimate', now, now, now,
          inp, out, 0, 0, rea, tool, 0, total, 'ESTIMATED', cost, None, 'ESTIMATED',
          f'dsh-session-activity estimator: {calls} assistant messages'))
conn.commit()
print('upserted', len(rows), 'estimated usage samples')
conn.close()