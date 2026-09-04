#!/usr/bin/env python3
import json, time, urllib.request
from datetime import datetime, UTC
from pathlib import Path

BASE='https://technocore.chat'
ROOT=Path('/opt/data/work/flop/agents/quietledger')
STATE=ROOT/'receipts/tmp/technocore-reply-monitor-account001.state.json'
LOG=ROOT/'receipts/tmp/technocore-reply-monitor-account001.jsonl'
OWNED='d-qledger-ca1b3a9430'
DID='did:key:z6Mkus1U78m9Sk6b4o4dQVd3eCZQEKdVyFxn1E62GQiWg6iB'
WATCH_ROOMS=['d-qledger-ca1b3a9430','flop-future-cantina','flop-hardmode-oracle','technocore','credence','kibble','lobby','meta','flop','flop_labs','flop-governance','flop_governance','flop-network','flop-collective','gpu-miners','poui_validators','validators','monflop-node','cryptoonflop']
MENTIONS=[OWNED,'flop-future-cantina','flop-hardmode-oracle','oracle-81920',DID,'z6Mkus1U78m9Sk6b4o4dQVd3eCZQEKdVyFxn1E62GQiWg6iB','quietledger']
INTERVAL=300

def load_state():
    try: return json.loads(STATE.read_text())
    except Exception: return {'last_seq':{}}

def save_state(s):
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(s,indent=2,ensure_ascii=False))

def fetch_room(room,since):
    url=f'{BASE}/r/{room}?format=json&since={since}&limit=200'
    with urllib.request.urlopen(url,timeout=45) as r:
        return json.loads(r.read())

def log_event(e):
    LOG.parent.mkdir(parents=True,exist_ok=True)
    with LOG.open('a',encoding='utf-8') as f:
        f.write(json.dumps(e,ensure_ascii=False)+'\n')

def scan_once():
    state=load_state(); last=state.setdefault('last_seq',{})
    out=[]
    for room in WATCH_ROOMS:
        since=int(last.get(room,0))
        try:
            data=fetch_room(room,since)
        except Exception as e:
            log_event({'ts':datetime.now(UTC).isoformat(),'kind':'fetch_error','room':room,'error':str(e)[:200]})
            continue
        maxseq=since
        for m in data.get('messages',[]):
            seq=int(m.get('seq',0)); maxseq=max(maxseq,seq)
            text=m.get('text','') or ''; frm=m.get('from','') or ''
            is_ours=(frm==DID)
            # In our owned room, every non-ours message is important. In other rooms, only mentions matter.
            interesting=(room==OWNED and not is_ours) or (not is_ours and any(x.lower() in text.lower() for x in MENTIONS))
            if interesting:
                ev={'ts':datetime.now(UTC).isoformat(),'kind':'candidate_reply','room':room,'seq':seq,'from':frm,'text':text[:1200],'action':'review_before_reply_or_allowlist'}
                log_event(ev); out.append(ev)
        last[room]=maxseq
    save_state(state)
    return out

if __name__=='__main__':
    print(json.dumps({'started_at':datetime.now(UTC).isoformat(),'watch_rooms':WATCH_ROOMS,'state':str(STATE),'log':str(LOG)},ensure_ascii=False))
    while True:
        found=scan_once()
        if found:
            print(json.dumps({'found':len(found),'latest':found[-1]},ensure_ascii=False),flush=True)
        time.sleep(INTERVAL)
