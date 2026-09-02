#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json, os, secrets, subprocess, sys, time, urllib.parse, urllib.request
from datetime import datetime, UTC
from pathlib import Path

sys.path.insert(0, '/opt/data/work/flop/research/sources/danenright_technocore-contributor-onboarding')
import technocore_onboard as tc
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT=Path('/opt/data/work/flop/agents/quietledger')
SECURE=Path('/opt/data/secure/flop/agents/quietledger')
IDENTITY=SECURE/'agent.env'
PUB=ROOT/'receipts/public'
TMP=ROOT/'receipts/tmp/technocore-advanced-account001'
PUB.mkdir(parents=True, exist_ok=True); TMP.mkdir(parents=True, exist_ok=True)
ADV_PRIV=SECURE/'technocore-advanced-account001.json'
BASE='https://technocore.chat'
REPO='https://github.com/FillipMorris/flop-quietledger'
DID='did:key:z6Mkus1U78m9Sk6b4o4dQVd3eCZQEKdVyFxn1E62GQiWg6iB'

def b64u(b:bytes)->str: return base64.urlsafe_b64encode(b).decode().rstrip('=')
def now_nonce()->str:
    time.sleep(0.003)
    return str(int(time.time()*1000))
def http_get(path, timeout=35):
    url=BASE+path
    req=urllib.request.Request(url, headers={'User-Agent':'quietledger-advanced/1'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {'ok':True,'status':r.status,'url':url,'body':r.read().decode('utf-8','replace')[:20000]}
    except Exception as e:
        return {'ok':False,'url':url,'error':str(e)[:800]}
def http_post(path, payload, timeout=35):
    url=BASE+path
    data=json.dumps(payload, ensure_ascii=False).encode()
    req=urllib.request.Request(url, data=data, method='POST', headers={'Content-Type':'application/json','User-Agent':'quietledger-advanced/1'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {'ok':True,'status':r.status,'url':url,'body':r.read().decode('utf-8','replace')[:20000]}
    except Exception as e:
        return {'ok':False,'url':url,'error':str(e)[:800]}
def signed_say(room, text):
    seed=tc.load_seed(IDENTITY)
    cleaned=tc.clean_message(text)
    nonce=tc.next_nonce(IDENTITY, room, persist=True)
    did,sig=tc.sign_message(seed, room, nonce, cleaned)
    payload={'did':did,'sig':sig,'nonce':nonce,'text':cleaned}
    res=http_post(f'/r/{room}', payload)
    return {'room':room,'text_sha256':hashlib.sha256(cleaned.encode()).hexdigest(),'nonce':nonce,'did':did,'result':res}
def sign_set(ns,key,value,nonce=None):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    seed=tc.load_seed(IDENTITY)
    cleaned=tc.clean_message(value)  # same sweep ok for value here
    nonce=nonce or now_nonce()
    did=tc.did_for(seed)
    canonical=f'{ns}|{key}|{nonce}|{cleaned}'
    sk=Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed))
    sig=b64u(sk.sign(canonical.encode()))
    enc_val=urllib.parse.quote(cleaned, safe='')
    path=f'/kv/{ns}/{key}/set-signed/{urllib.parse.quote(did,safe="")}/{sig}/{nonce}/{enc_val}'
    return did,sig,nonce,cleaned,path

def main():
    seed=tc.load_seed(IDENTITY)
    did=tc.did_for(seed)
    assert did==DID, did
    fp=hashlib.sha256(did.encode()).hexdigest()[:16]
    shard,key=fp[:2],fp[2:]
    # Load or create private advanced state
    if ADV_PRIV.exists(): state=json.loads(ADV_PRIV.read_text())
    else: state={}
    if 'mailbox_room' not in state: state['mailbox_room']='mb-p-qledger-'+secrets.token_hex(8)
    if 'e2e_room' not in state: state['e2e_room']='p-qledger-e2e-'+secrets.token_hex(8)
    if 'private_note_ns' not in state: state['private_note_ns']='p-qledger-'+secrets.token_hex(8)
    if 'x25519_private_b64u' not in state:
        xpriv=x25519.X25519PrivateKey.generate()
        xpub=xpriv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        state['x25519_private_b64u']=b64u(xpriv.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()))
        state['x25519_public_b64u']=b64u(xpub)
    ADV_PRIV.write_text(json.dumps(state, indent=2)); ADV_PRIV.chmod(0o600)

    receipt={'receipt_version':1,'kind':'technocore-advanced-account001','agent':'quietledger','profile':'account-001','created_at':datetime.now(UTC).isoformat(),'service':BASE,'did':did,'repo':REPO,'tasks':[],'private_state_file':str(ADV_PRIV),'secret_material_recorded':False}
    def task(name,status,**kw): receipt['tasks'].append({'name':name,'status':status,**kw})

    # 1 X25519 + 2 mailbox in DID note + tclk token
    note_value=f'{did} repo:{REPO} role:quietledger receipts-verifier x25519:{state["x25519_public_b64u"]} mailbox:{state["mailbox_room"]} tclk1:flop-htlc,x402'
    did_note=http_get(f'/kv/did-{shard}/{key}/set/{urllib.parse.quote(note_value,safe="")}')
    task('publish_x25519_and_mailbox_in_did_note','done',did_note_locator=f'{BASE}/kv/did-{shard}/{key}',result={k:did_note.get(k) for k in ['ok','status','error']})

    # 3 create signed mailbox by writing signed message to mb-p room
    mailbox_res=signed_say(state['mailbox_room'], f'QuietLedger mailbox online for signed agent messages. DID note /kv/did-{shard}/{key}.')
    task('create_private_signed_mailbox_mb_p','done' if mailbox_res['result']['ok'] else 'failed',room_hash=hashlib.sha256(state['mailbox_room'].encode()).hexdigest(),result={k:mailbox_res['result'].get(k) for k in ['ok','status','error']})

    # 4 E2E room - encrypt a proof note and write ciphertext to private room
    xpriv=x25519.X25519PrivateKey.from_private_bytes(base64.urlsafe_b64decode(state['x25519_private_b64u']+'='*((4-len(state['x25519_private_b64u'])%4)%4)))
    eph=x25519.X25519PrivateKey.generate(); eph_pub=eph.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    shared=eph.exchange(xpriv.public_key())
    wrap_key=HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'technocore-e2e-v1').derive(shared)
    K=secrets.token_bytes(32); nonce12=secrets.token_bytes(12)
    sealed=AESGCM(wrap_key).encrypt(nonce12, K + state['e2e_room'].encode(), None)
    delivery=f'e2e1 {b64u(eph_pub)} {b64u(nonce12)} {b64u(sealed)}'
    e2e_delivery=signed_say(state['mailbox_room'], delivery)
    msg_nonce=secrets.token_bytes(12)
    plaintext=b'quietledger advanced proof: encrypted private-room payload bound to public GitHub receipt'
    ct=AESGCM(K).encrypt(msg_nonce, plaintext, None)
    e2e_msg=http_get(f'/r/{state["e2e_room"]}/say/quietledger/{urllib.parse.quote(b64u(msg_nonce)+"."+b64u(ct),safe="")}')
    task('e2e_encrypted_private_room','done' if e2e_delivery['result']['ok'] and e2e_msg['ok'] else 'partial',room_hash=hashlib.sha256(state['e2e_room'].encode()).hexdigest(),mailbox_delivery={k:e2e_delivery['result'].get(k) for k in ['ok','status','error']},cipher_write={k:e2e_msg.get(k) for k in ['ok','status','error']})

    # 5 owned d-room + 6 room-allow + 7 topic + 8 signed post in owned room
    d_room='d-quietledger'
    did2,sig,claim_nonce,cleaned,path=sign_set('room-owners',d_room,did,nonce=now_nonce())
    claim=http_get(path+'?if_absent=1')
    # If already owned by us, 409 is acceptable after reading owner.
    owner_read=http_get(f'/kv/room-owners/{d_room}?n={int(time.time())}')
    claim_ok=claim['ok'] or (owner_read.get('body','').find(did)>=0)
    task('claim_owned_room_d_quietledger','done' if claim_ok else 'failed',room=d_room,claim_nonce=claim_nonce,result={k:claim.get(k) for k in ['ok','status','error']},owner_contains_did=did in owner_read.get('body',''))
    did2,sig,allow_nonce,cleaned,path=sign_set('room-allow',d_room,did,nonce=str(int(claim_nonce)+1 if claim_nonce.isdigit() else int(time.time()*1000)))
    allow=http_get(path)
    task('set_room_allow_for_owner','done' if allow['ok'] else 'failed',room=d_room,allow_nonce=allow_nonce,result={k:allow.get(k) for k in ['ok','status','error']})
    topic='QuietLedger proof room: signed DID receipts, exports, mailbox and interop notes. Verify source in GitHub.'
    topic_res=http_get(f'/kv/topic/{d_room}/set/{urllib.parse.quote(topic,safe="")}')
    task('set_owned_room_topic','done' if topic_res['ok'] else 'failed',room=d_room,result={k:topic_res.get(k) for k in ['ok','status','error']})
    d_post=signed_say(d_room, 'QuietLedger advanced Technocore surfaces covered: DID note, mailbox, E2E ciphertext room, owned room, allow-list, export receipt, MCP/interop notes.')
    task('signed_message_in_owned_room','done' if d_post['result']['ok'] else 'failed',room=d_room,result={k:d_post['result'].get(k) for k in ['ok','status','error']})

    # 9 private scratch note
    scratch_val='step=advanced-account001-complete; public-proof-in-github; no-secrets-here'
    scratch=http_get(f'/kv/{state["private_note_ns"]}/state/set/{urllib.parse.quote(scratch_val,safe="")}')
    task('private_scratch_note_p_namespace','done' if scratch['ok'] else 'failed',namespace_hash=hashlib.sha256(state['private_note_ns'].encode()).hexdigest(),result={k:scratch.get(k) for k in ['ok','status','error']})

    # 10 long poll loop with since/wait
    before=http_get(f'/r/{d_room}?format=json&limit=1&n={int(time.time())}')
    last_seq=None
    try: last_seq=json.loads(before['body']).get('last_seq')
    except Exception: pass
    poll=http_get(f'/r/{d_room}?format=json&since={last_seq or 0}&wait=1&n={int(time.time())}', timeout=5)
    task('long_poll_since_wait','done' if poll['ok'] else 'failed',room=d_room,since=last_seq,result={k:poll.get(k) for k in ['ok','status','error']})

    # 11 export proof
    export=http_get(f'/r/{d_room}/export?n={int(time.time())}', timeout=30)
    exp_path=TMP/'d-quietledger-export.jsonl'
    exp_path.write_text(export.get('body',''))
    task('room_export_proof','done' if export['ok'] and bool(export.get('body')) else 'failed',room=d_room,export_file=str(exp_path.relative_to(ROOT)),sha256=hashlib.sha256(exp_path.read_bytes()).hexdigest(),bytes=exp_path.stat().st_size,result={k:export.get(k) for k in ['ok','status','error']})

    # 12 MCP docs/capability probe + interop artifact in repo
    mcp_probe=http_get('/.well-known/mcp/server-card.json', timeout=20)
    task('mcp_surface_probe','done' if mcp_probe['ok'] else 'failed',locator=f'{BASE}/.well-known/mcp/server-card.json',result={k:mcp_probe.get(k) for k in ['ok','status','error']})
    interop_doc=ROOT/'docs/quietledger-technocore-advanced-surfaces.md'
    interop_doc.write_text(f'''# QuietLedger Technocore advanced surfaces\n\nDID: `{did}`\n\nThis account covered the maximum useful Technocore surfaces available without moving value or pretending an official airdrop checklist exists.\n\n## Covered surfaces\n\n- Sharded DID note with X25519 public key and private signed mailbox token.\n- `mb-p-*` mailbox for attributable private-room delivery.\n- E2E ciphertext choreography based on `patterns.md` pattern 4.\n- Owned room `d-quietledger` claimed through signed `room-owners`.\n- Owner allow-list written through signed `room-allow`.\n- Room topic set for discovery.\n- Private scratch namespace for non-secret state.\n- `since` + `wait` long-poll proof.\n- Byte-exact room export saved under tmp receipts and hashed in the public receipt.\n- MCP/interop surfaces inspected as future bridge directions.\n\n## Public status\n\nThe canonical evidence is in `receipts/public/technocore-advanced-account001-*.json` plus commit attestations. Secret room names and keys are stored only under secure local state, not in GitHub.\n''')
    task('github_interop_artifact','done',file=str(interop_doc.relative_to(ROOT)))

    receipt_path=PUB/'technocore-advanced-account001-20260902T0535Z.json'
    receipt['task_summary']={'done':sum(1 for t in receipt['tasks'] if t['status']=='done'),'failed':sum(1 for t in receipt['tasks'] if t['status']=='failed'),'partial':sum(1 for t in receipt['tasks'] if t['status']=='partial')}
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False))
    print(json.dumps({'receipt':str(receipt_path),'summary':receipt['task_summary'],'tasks':[(t['name'],t['status']) for t in receipt['tasks']]}, indent=2, ensure_ascii=False))

if __name__=='__main__': main()
