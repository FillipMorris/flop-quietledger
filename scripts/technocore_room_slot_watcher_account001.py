#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, time
from datetime import datetime, UTC
from pathlib import Path

ROOT=Path('/opt/data/work/flop/agents/quietledger')
LOG=ROOT/'receipts/tmp/technocore-room-slot-watcher-account001.log'
DONE=ROOT/'receipts/tmp/technocore-room-slot-watcher-account001.done'
INTERVAL=600
DEADLINE=time.time()+24*3600

def stamp(): return datetime.now(UTC).isoformat()

def log(s):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a',encoding='utf-8') as f: f.write(f'[{stamp()}] {s}\n')

log('watcher started: retry every 600s, max 24h')
while time.time()<DEADLINE:
    p=subprocess.run(['/opt/hermes/.venv/bin/python','scripts/technocore_advanced_account001_fix.py'],cwd=str(ROOT),text=True,capture_output=True,timeout=420)
    log(f'exit={p.returncode} stdout={p.stdout.strip()!r} stderr={p.stderr.strip()[:500]!r}')
    # success condition: newest public receipt says mailbox/owned-room no longer hit room limit
    receipts=sorted((ROOT/'receipts/public').glob('technocore-advanced-account001-*.json'))
    if receipts:
        data=json.loads(receipts[-1].read_text())
        bodies=json.dumps(data,ensure_ascii=False)
        if 'room limit reached' not in bodies and 'The read operation timed out' not in bodies:
            DONE.write_text(f'done at {stamp()} receipt={receipts[-1]}\n')
            log(f'DONE receipt={receipts[-1]}')
            raise SystemExit(0)
    time.sleep(INTERVAL)
log('timeout 24h without available room slot')
raise SystemExit(2)
