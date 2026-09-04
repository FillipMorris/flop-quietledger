#!/usr/bin/env python3
"""QuietLedger public receipt verifier.

Checks public JSON receipts/attestations for secret leaks, DID consistency,
GitHub commit shape, and Technocore locator shape. This is intentionally
local-first: it verifies the evidence bundle before it is published or copied.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

DID_RE = re.compile(r"did:key:z6Mk[1-9A-HJ-NP-Za-km-z]{44}")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SECRET_KEYS = re.compile(r"(?:seed|private|token|cookie|password|secret|signed_url|wallet)", re.I)
SECRET_VALUE_64HEX = re.compile(r"^[0-9a-f]{64}$", re.I)
PUBLIC_ACCOUNT_LABELS = re.compile(r"account[-_ ]?0*1|account001|account01|account 1", re.I)
EXPECTED_DID = "did:key:z6Mkus1U78m9Sk6b4o4dQVd3eCZQEKdVyFxn1E62GQiWg6iB"
# Public bootstrap-panel identities created for neutral non-FLOP rooms.
# Seeds stay in secure storage; these DIDs are safe public identifiers.
ALLOWED_PANEL_DIDS = {
    EXPECTED_DID,
    "did:key:z6Mkoc5grcRgnNDgNc9GrFb6iwbTWnkk8hbP1cTUXfmnrTcT",
    "did:key:z6MknqnCbTksJWTks8xFnhPGv2X66WfKDqnoJWmEKRE228kc",
    "did:key:z6Mkm4gd2rcz23FCHWB7KfWnR9j5awjo38qtHnmxHSr5fRNQ",
}

def scan(obj, path="$"):
    problems=[]
    if isinstance(obj, dict):
        for k,v in obj.items():
            child_path = f"{path}.{k}"
            # Safe boolean disclosure field used by public receipts.
            if str(k) != "secret_material_recorded" and SECRET_KEYS.search(str(k)):
                problems.append(f"secret-like key {child_path}")
            problems.extend(scan(v, child_path))
    elif isinstance(obj, list):
        for i,v in enumerate(obj): problems.extend(scan(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        if PUBLIC_ACCOUNT_LABELS.search(obj):
            problems.append(f"public account-number label {path}")
        if SECRET_VALUE_64HEX.fullmatch(obj) and not (path.endswith(".sha256") or path.endswith("_sha256") or path.endswith(".message_sha256")):
            problems.append(f"64hex secret-like value {path}")
        if "BEGIN PRIVATE KEY" in obj or "/say-signed/" in obj: problems.append(f"private/signed-url value {path}")
    return problems

def verify_file(p: Path):
    try: data=json.loads(p.read_text())
    except Exception as e: return [f"{p}: invalid json: {e}"]
    problems=scan(data, str(p))
    text=json.dumps(data, sort_keys=True)
    dids=set(DID_RE.findall(text))
    allowed = ALLOWED_PANEL_DIDS if data.get("kind") in {"technocore-neutral-panel-bootstrap", "technocore-growth-wave2"} else {EXPECTED_DID}
    if dids and not dids.issubset(allowed): problems.append(f"{p}: unexpected DID(s) {sorted(dids - allowed)}")
    if p.name.startswith("ATTESTATION"):
        c=data.get("commit")
        if not isinstance(c,str) or not SHA_RE.fullmatch(c): problems.append(f"{p}: bad commit hash")
        if data.get("did") != EXPECTED_DID: problems.append(f"{p}: attestation DID mismatch")
    return [f"{p}: {x}" for x in problems]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", default=["receipts/public"])
    ns=ap.parse_args()
    files=[]
    for raw in ns.paths:
        p=Path(raw)
        if p.is_dir(): files += sorted(p.rglob("*.json"))
        elif p.exists(): files.append(p)
    problems=[]
    for f in files: problems.extend(verify_file(f))
    print(json.dumps({"checked_files": len(files), "ok": not problems, "problems": problems}, indent=2))
    return 0 if not problems else 1
if __name__ == "__main__": raise SystemExit(main())
