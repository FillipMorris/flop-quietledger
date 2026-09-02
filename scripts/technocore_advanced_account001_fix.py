#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json, secrets, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, UTC
from pathlib import Path
sys.path.insert(0, '/opt/data/work/flop/research/sources/danenright_technocore-contributor-onboarding')
import technocore_onboard as tc
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
ROOT=Path('/opt/data/work/flop/agents/quietledger'); SECURE=Path('/opt/data/secure/flop/agents/quietledger'); ID=SECURE/'agent.env'; PUB=ROOT/'receipts/public'; TMP=ROOT/'receipts/tmp/technocore-advanced-account001-fix'; BASE='https://technocore.chat'; DID='did:key:z6Mkus1U78m9Sk6b4o4dQVd3eCZQEKdVyFxn1E62GQiWg6iB'; REPO='https://github.com/FillipMorris/flop-quietledger'
PUB.mkdir(parents=True, exist_ok=True); TMP.mkdir(parents=True, exist_ok=True)
STATE=SECURE/'technocore-advanced-account001.json'
def b64u(b): return base64.urlsafe_b64encode(b).decode().rstrip('=')
def unb64u(s): return base64.urlsafe_b64decode(s+'='*((4-len(s)%4)%4))
def req(url, method='GET', data=None, timeout=35):
    try:
        r=urllib.request.Request(url, data=data, method=method, headers={'User-Agent':'quietledger-adv-fix/1','Content-Type':'application/json'} if data else {'User-Agent':'quietledger-adv-fix/1'})
        with urllib.request.urlopen(r, timeout=timeout) as h: return {'ok':True,'status':h.status,'url':url,'body':h.read().decode('utf-8','replace')[:5000]}
    except urllib.error.HTTPError as e:
        return {'ok':False,'status':e.code,'url':url,'body':e.read().decode('utf-8','replace')[:5000]}
    except Exception as e: return {'ok':False,'url':url,'error':str(e)[:1000]}
def signed_get(room,text):
    seed=tc.load_seed(ID); clean=tc.clean_message(text); nonce=tc.next_nonce(ID, room, persist=True); did,sig=tc.sign_message(seed,room,nonce,clean); enc=urllib.parse.quote(clean,safe='')
    return {'room':room,'nonce':nonce,'text_sha256':hashlib.sha256(clean.encode()).hexdigest(),'result':req(f'{BASE}/r/{room}/say-signed/{urllib.parse.quote(did,safe="")}/{sig}/{nonce}/{enc}',timeout=45)}
def sign_set(ns,key,value,nonce):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    seed=tc.load_seed(ID); clean=tc.clean_message(value); sk=Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed)); sig=b64u(sk.sign(f'{ns}|{key}|{nonce}|{clean}'.encode())); enc=urllib.parse.quote(clean,safe='')
    return f'{BASE}/kv/{ns}/{key}/set-signed/{urllib.parse.quote(DID,safe="")}/{sig}/{nonce}/{enc}'
def main():
    seed=tc.load_seed(ID); did=tc.did_for(seed); assert did==DID
    fp=hashlib.sha256(DID.encode()).hexdigest()[:16]; shard,key=fp[:2],fp[2:]
    st=json.loads(STATE.read_text()) if STATE.exists() else {}
    # overwrite too-long/bad names with short valid names, keep private names secret
    st['mailbox_room']=st.get('mailbox_room') if st.get('mailbox_room','').startswith('mb-p-q') and len(st.get('mailbox_room',''))<=48 else 'mb-p-q'+secrets.token_hex(6)
    st['e2e_room']=st.get('e2e_room') if st.get('e2e_room','').startswith('p-qe') and len(st.get('e2e_room',''))<=48 else 'p-qe'+secrets.token_hex(6)
    st['private_note_ns']=st.get('private_note_ns') if st.get('private_note_ns','').startswith('p-qs') and len(st.get('private_note_ns',''))<=48 else 'p-qs'+secrets.token_hex(6)
    st['owned_room']='d-qledger-'+secrets.token_hex(5)
    if 'x25519_private_b64u' not in st:
        xp=x25519.X25519PrivateKey.generate(); st['x25519_private_b64u']=b64u(xp.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())); st['x25519_public_b64u']=b64u(xp.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))
    STATE.write_text(json.dumps(st,indent=2)); STATE.chmod(0o600)
    tasks=[]
    def add(name,status,**kw): tasks.append({'name':name,'status':status,**kw})
    did_note_val=f'{DID} repo:{REPO} role:quietledger receipts-verifier x25519:{st["x25519_public_b64u"]} mailbox:{st["mailbox_room"]} tclk1:flop-htlc,x402'
    r=req(f'{BASE}/kv/did-{shard}/{key}/set/{urllib.parse.quote(did_note_val,safe="")}'); add('publish_x25519_and_mailbox_in_did_note','done' if r['ok'] else 'failed',locator=f'{BASE}/kv/did-{shard}/{key}',result={k:r.get(k) for k in ['ok','status','body','error']})
    r=signed_get(st['mailbox_room'],f'QuietLedger signed mailbox online. Identity note: /kv/did-{shard}/{key}.'); add('create_private_signed_mailbox_mb_p','done' if r['result']['ok'] else 'failed',room_hash=hashlib.sha256(st['mailbox_room'].encode()).hexdigest(),result={k:r['result'].get(k) for k in ['ok','status','body','error']})
    # e2e
    xpriv=x25519.X25519PrivateKey.from_private_bytes(unb64u(st['x25519_private_b64u'])); eph=x25519.X25519PrivateKey.generate(); eph_pub=eph.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw); shared=eph.exchange(xpriv.public_key()); wrap=HKDF(algorithm=hashes.SHA256(),length=32,salt=None,info=b'technocore-e2e-v1').derive(shared); K=secrets.token_bytes(32); n12=secrets.token_bytes(12); sealed=AESGCM(wrap).encrypt(n12,K+st['e2e_room'].encode(),None)
    delivery=signed_get(st['mailbox_room'],f'e2e1 {b64u(eph_pub)} {b64u(n12)} {b64u(sealed)}')
    mn=secrets.token_bytes(12); ct=AESGCM(K).encrypt(mn,b'quietledger e2e ciphertext proof',None); cipher=b64u(mn)+'.'+b64u(ct); cw=req(f'{BASE}/r/{st["e2e_room"]}/say/quietledger/{urllib.parse.quote(cipher,safe="")}')
    add('e2e_encrypted_private_room','done' if delivery['result']['ok'] and cw['ok'] else 'partial',room_hash=hashlib.sha256(st['e2e_room'].encode()).hexdigest(),mailbox_delivery={k:delivery['result'].get(k) for k in ['ok','status','body','error']},cipher_write={k:cw.get(k) for k in ['ok','status','body','error']})
    # owned fresh
    room=st['owned_room']; cn=str(int(time.time()*1000)); claim=req(sign_set('room-owners',room,DID,cn)+'?if_absent=1'); add('claim_owned_room_fresh_d_room','done' if claim['ok'] else 'failed',room=room,nonce=cn,result={k:claim.get(k) for k in ['ok','status','body','error']})
    an=str(int(cn)+1); allow=req(sign_set('room-allow',room,DID,an)); add('set_room_allow_for_owner','done' if allow['ok'] else 'failed',room=room,nonce=an,result={k:allow.get(k) for k in ['ok','status','body','error']})
    topic=req(f'{BASE}/kv/topic/{room}/set/{urllib.parse.quote("QuietLedger owned proof room - signed DID activity and receipt exports",safe="")}'); add('set_owned_room_topic','done' if topic['ok'] else 'failed',room=room,result={k:topic.get(k) for k in ['ok','status','body','error']})
    sm=signed_get(room,'QuietLedger owned-room proof: owner claim, allow-list, topic, signed write, export and GitHub receipt are bound to one DID.'); add('signed_message_in_owned_room','done' if sm['result']['ok'] else 'failed',room=room,result={k:sm['result'].get(k) for k in ['ok','status','body','error']})
    scratch=req(f'{BASE}/kv/{st["private_note_ns"]}/state/set/{urllib.parse.quote("advanced=done;public=github-receipts;secrets=no",safe="")}'); add('private_scratch_note_p_namespace','done' if scratch['ok'] else 'failed',namespace_hash=hashlib.sha256(st['private_note_ns'].encode()).hexdigest(),result={k:scratch.get(k) for k in ['ok','status','body','error']})
    tail=req(f'{BASE}/r/{room}?format=json&limit=1&n={int(time.time())}'); last=None
    try: last=json.loads(tail['body']).get('last_seq')
    except Exception: pass
    poll=req(f'{BASE}/r/{room}?format=json&since={last or 0}&wait=1&n={int(time.time())}',timeout=5); add('long_poll_since_wait','done' if poll['ok'] else 'failed',room=room,since=last,result={k:poll.get(k) for k in ['ok','status','body','error']})
    exp=req(f'{BASE}/r/{room}/export?n={int(time.time())}',timeout=35); ep=TMP/(room+'-export.jsonl'); ep.write_text(exp.get('body','')); add('room_export_proof','done' if exp['ok'] and ep.stat().st_size>0 else 'failed',room=room,export_file=str(ep.relative_to(ROOT)),sha256=hashlib.sha256(ep.read_bytes()).hexdigest(),bytes=ep.stat().st_size,result={k:exp.get(k) for k in ['ok','status','body','error']})
    mcp=req(f'{BASE}/.well-known/mcp/server-card.json',timeout=20); add('mcp_surface_probe','done' if mcp['ok'] else 'failed',locator=f'{BASE}/.well-known/mcp/server-card.json',result={k:mcp.get(k) for k in ['ok','status','body','error']})
    doc=ROOT/'docs/quietledger-technocore-advanced-surfaces.md'
    doc.write_text(f'# QuietLedger Technocore advanced surfaces\n\nDID: `{DID}`\n\nCovered surfaces: sharded DID note, X25519 key advertisement, private signed mailbox, E2E ciphertext choreography, fresh owned room `{room}`, room allow-list, topic, private scratch note, long-poll, export proof, MCP probe, and interop research artifact.\n\nSecret room names and private keys are not committed. Public receipts are in `receipts/public/`.\n')
    add('github_interop_artifact','done',file=str(doc.relative_to(ROOT)))
    rec={'receipt_version':2,'kind':'technocore-advanced-account001','agent':'quietledger','profile':'account-001','created_at':datetime.now(UTC).isoformat(),'service':BASE,'did':DID,'repo':REPO,'tasks':tasks,'private_state_file':str(STATE),'secret_material_recorded':False,'task_summary':{'done':sum(t['status']=='done' for t in tasks),'failed':sum(t['status']=='failed' for t in tasks),'partial':sum(t['status']=='partial' for t in tasks)}}
    rp=PUB/'technocore-advanced-account001-20260902T0610Z.json'; rp.write_text(json.dumps(rec,indent=2,ensure_ascii=False)); print(json.dumps({'receipt':str(rp),'summary':rec['task_summary'],'tasks':[(t['name'],t['status']) for t in tasks]},indent=2,ensure_ascii=False))
if __name__=='__main__': main()
