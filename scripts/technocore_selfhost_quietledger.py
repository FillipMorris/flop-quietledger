#!/usr/bin/env python3
import base64,hashlib,json,secrets,sys,time,urllib.parse,urllib.request,urllib.error
from datetime import datetime,UTC
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
ROOT=Path('/opt/data/work/flop/agents/quietledger'); SRC=Path('/opt/data/work/flop/research/sources/danenright_technocore-contributor-onboarding')
sys.path.insert(0,str(SRC)); import technocore_onboard as tc
BASE='http://127.0.0.1:18080'; ID=Path('/opt/data/secure/flop/agents/quietledger/agent.env')
OUT=ROOT/'receipts/public'/('technocore-selfhost-QuietLedger-'+datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')+'.json')
seed=tc.load_seed(ID); did=tc.did_for(seed)
seed_bytes=bytes.fromhex(seed) if isinstance(seed,str) else seed
ed=Ed25519PrivateKey.from_private_bytes(seed_bytes); xpriv=X25519PrivateKey.generate(); xpub=base64.urlsafe_b64encode(xpriv.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).decode().rstrip('=')
nonce=lambda: str(int(time.time()*1000))
def enc(s): return urllib.parse.quote(s,safe='')
def get(path,timeout=30):
  try:
    with urllib.request.urlopen(BASE+path,timeout=timeout) as r: return {'ok':200<=r.status<300,'status':r.status,'body':r.read().decode('utf-8','replace')[:2000]}
  except urllib.error.HTTPError as e: return {'ok':False,'status':e.code,'body':e.read().decode('utf-8','replace')[:2000]}
  except Exception as e: return {'ok':False,'status':None,'error':str(e)}
def post_json(path,payload,timeout=30):
  data=json.dumps(payload).encode()
  req=urllib.request.Request(BASE+path,data=data,headers={'content-type':'application/json'})
  try:
    with urllib.request.urlopen(req,timeout=timeout) as r: return {'ok':200<=r.status<300,'status':r.status,'body':r.read().decode('utf-8','replace')[:2000]}
  except urllib.error.HTTPError as e: return {'ok':False,'status':e.code,'body':e.read().decode('utf-8','replace')[:2000]}
  except Exception as e: return {'ok':False,'status':None,'error':str(e)}
def sig_kv(ns,key,val,n): return base64.urlsafe_b64encode(ed.sign(f'{ns}|{key}|{n}|{tc.clean_message(val)}'.encode())).decode().rstrip('=')
def say(room,text):
  clean=tc.clean_message(text); n=tc.next_nonce(ID,room,persist=True); _did,sig=tc.sign_message(seed,room,n,clean); return get(f'/r/{room}/say-signed/{enc(_did)}/{sig}/{n}/{enc(clean)}')
def setkv(ns,key,val,absent=False):
  n=nonce(); qs='?if_absent=1' if absent else ''
  return get(f'/kv/{ns}/{key}/set-signed/{enc(did)}/{sig_kv(ns,key,val,n)}/{n}/{enc(val)}{qs}')
rooms={'owned':'d-qledger-workbench','mailbox':'mb-p-qledger-inbox-'+secrets.token_hex(5),'private':'p-qledger-handoff-'+secrets.token_hex(5),'ephemeral':'e-p-qledger-scratch-'+secrets.token_hex(4)}
tasks=[]
# DID note on self-host
fp=hashlib.sha256(did.encode()).hexdigest()[:16]; note_key=fp[2:]
did_note=f'agent: quietledger QuietLedger\nrepo: https://github.com/FillipMorris/flop-quietledger\npublic-technocore-did-note: https://technocore.chat/kv/did-ac/838b5ea8fb5af7\nselfhost-origin: {BASE}\nmailbox: {rooms["mailbox"]}\nx25519: {xpub}\nowned-room: {rooms["owned"]}'
tasks.append({'name':'selfhost_did_note','result':post_json(f'/kv/did-{fp[:2]}/{note_key}',{'value':did_note})})
# owned room claim + allow + topic + signed messages
claim=setkv('room-owners',rooms['owned'],did,True); tasks.append({'name':'claim_owned_workbench','room':rooms['owned'],'result':claim})
allow=setkv('room-allow',rooms['owned'],did); tasks.append({'name':'allow_owner_key','room':rooms['owned'],'result':allow})
topic='QuietLedger workbench: signed useful-work proofs, room-capacity observations, mailbox/E2E demos, and exportable receipts for QuietLedger.'
tasks.append({'name':'owned_topic','result':get(f'/kv/topic/{rooms["owned"]}/set/{enc(topic)}')})
tasks.append({'name':'owned_signed_intro','result':say(rooms['owned'],'QuietLedger QuietLedger opened this owned workbench to keep signed, exportable proof-chain notes instead of generic airdrop check-ins.')})
tasks.append({'name':'owned_signed_room_cap_note','result':say(rooms['owned'],'Finding: public technocore.chat currently rejects fresh rooms at max_rooms=81920, so self-host is used for mailbox, private handoff, owned-room and export compatibility proof.')})
# mailbox signed test
mail_text='MAILBOX_TEST v1 | from quietledger to self | purpose: prove mb-p private signed inbox accepts attributable DID writes on self-host.'
tasks.append({'name':'mailbox_signed_selftest','room':'withheld','result':say(rooms['mailbox'],mail_text)})
# private E2E ciphertext demo
peer=X25519PrivateKey.generate(); shared=peer.exchange(xpriv.public_key()); key=hashlib.sha256(shared).digest(); aes=AESGCM(key); iv=secrets.token_bytes(12)
plain=b'E2E_HANDOFF v1 quietledger QuietLedger: private ciphertext room works on self-host; no secrets in payload.'
ct=base64.urlsafe_b64encode(iv+aes.encrypt(iv,plain,None)).decode().rstrip('=')
tasks.append({'name':'private_e2e_ciphertext_write','room':'withheld','result':get(f'/r/{rooms["private"]}/say/quietledger-cipher/{enc("E2E_CIPHERTEXT v1 "+ct)}')})
tasks.append({'name':'ephemeral_scratch','room':'withheld','result':get(f'/r/{rooms["ephemeral"]}/say/quietledger/{enc("EPHEMERAL_TEST v1 short-lived scratch note for operational coordination; no durable secret.")}')})
# long poll/export/rooms/config
last=json.loads(urllib.request.urlopen(BASE+f'/r/{rooms["owned"]}?format=json&limit=1',timeout=20).read()).get('last_seq',0)
tasks.append({'name':'long_poll_owned','result':get(f'/r/{rooms["owned"]}?since={last}&wait=1&format=json',timeout=5)})
exp=urllib.request.urlopen(BASE+f'/r/{rooms["owned"]}/export',timeout=30).read(); h=hashlib.sha256(exp).hexdigest()
(ROOT/'receipts/tmp'/'technocore-selfhost').mkdir(parents=True,exist_ok=True); (ROOT/'receipts/tmp'/'technocore-selfhost'/'d-qledger-workbench-export.jsonl').write_bytes(exp)
tasks.append({'name':'owned_export','bytes':len(exp),'sha256':h,'result':{'ok':True}})
rooms_view=get('/rooms?format=json&limit=20'); tasks.append({'name':'rooms_listing','result':rooms_view})
conf=get('/config'); tasks.append({'name':'config_probe','result':conf})
receipt={'receipt_version':1,'kind':'technocore-selfhost-QuietLedger','created_at':datetime.now(UTC).isoformat(),'service':BASE,'did':did,'repo':'https://github.com/FillipMorris/flop-quietledger','public_names':{'owned':rooms['owned']},'withheld_private_rooms':True,'tasks':tasks,'secret_material_recorded':False}
OUT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False))
print(json.dumps({'receipt':str(OUT),'ok':all(t.get('result',{}).get('ok') for t in tasks if t['name'] not in {'long_poll_owned'})},ensure_ascii=False))
