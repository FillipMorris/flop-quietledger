#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path
sys.path.insert(0,'/opt/data/work/flop/research/sources/danenright_technocore-contributor-onboarding')
import technocore_onboard as tc
IDENTITY=Path('/opt/data/secure/flop/agents/quietledger/agent.env')

def envelope(room, text):
    seed=tc.load_seed(IDENTITY)
    cleaned=tc.clean_message(text)
    nonce=tc.next_nonce(IDENTITY, room, persist=True)
    did,sig=tc.sign_message(seed, room, nonce, cleaned)
    return {'did':did,'sig':sig,'nonce':nonce,'text':cleaned}

if __name__=='__main__':
    room=sys.argv[1]
    text=sys.argv[2]
    payload=envelope(room,text)
    tmp=Path('/tmp/quietledger_tc_payload.json')
    tmp.write_text(json.dumps(payload))
    tmp.chmod(0o600)
    try:
        r=subprocess.run(['curl','--http1.1','-m','35','-fsS','-X','POST','-H','Content-Type: application/json','--data-binary',f'@{tmp}',f'https://technocore.chat/r/{room}'],text=True,capture_output=True)
        print(json.dumps({'curl_exit':r.returncode,'stdout_len':len(r.stdout),'stderr':r.stderr[:200],'did':payload['did'],'nonce':payload['nonce'],'text':payload['text']},ensure_ascii=False))
    finally:
        tmp.unlink(missing_ok=True)
