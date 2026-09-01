#!/usr/bin/env python3
"""One-account FLOP/Technocore operator wrapper.

Wraps the audited local onboarding helper while keeping secrets out of the public worktree.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/opt/data/work/flop/agents/quietledger')
ONBOARD = Path('/opt/data/work/flop/research/sources/danenright_technocore-contributor-onboarding/technocore_onboard.py')
IDENTITY = Path('/opt/data/secure/flop/agents/quietledger/agent.env')
RECEIPTS = ROOT / 'receipts' / 'public'

INTRO_MESSAGE = (
    'quietledger/account01 online: one persistent DID for useful Technocore work; '
    'keeping public receipts, avoiding faucet spam and one-shot identity churn; '
    'will publish concise protocol observations and signed GitHub commit attestations.'
)

def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault('PYTHONUNBUFFERED', '1')
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env, text=True, capture_output=True)
    if check and proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.stderr.write(proc.stdout)
        raise SystemExit(proc.returncode)
    return proc

def onboard(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run([sys.executable, str(ONBOARD), '--identity', str(IDENTITY), *args], check=check)

def cmd_status(_: argparse.Namespace) -> None:
    data = {
        'root': str(ROOT),
        'identity_path': str(IDENTITY),
        'identity_exists': IDENTITY.exists(),
        'identity_mode': oct(IDENTITY.stat().st_mode & 0o777) if IDENTITY.exists() else None,
        'receipts_dir': str(RECEIPTS),
        'onboard_helper': str(ONBOARD),
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    if IDENTITY.exists():
        did = onboard('did').stdout.strip()
        data['did'] = did
    print(json.dumps(data, indent=2, ensure_ascii=False))

def cmd_init(_: argparse.Namespace) -> None:
    IDENTITY.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(IDENTITY.parent, 0o700)
    proc = onboard('init')
    if IDENTITY.exists():
        os.chmod(IDENTITY, 0o600)
    print(proc.stdout.strip())

def cmd_intro_dry(_: argparse.Namespace) -> None:
    proc = onboard('join', '--room', 'lobby', '--kind', 'introduction', '--message', INTRO_MESSAGE, '--dry-run')
    print(proc.stdout.strip())

def cmd_intro_publish(_: argparse.Namespace) -> None:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    receipt = RECEIPTS / f"introduction-lobby-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    proc = onboard('join', '--room', 'lobby', '--kind', 'introduction', '--message', INTRO_MESSAGE, '--receipt', str(receipt))
    print(proc.stdout.strip())

def cmd_attest(args: argparse.Namespace) -> None:
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    out = RECEIPTS / f"ATTESTATION-{args.commit[:12]}.json"
    proc = onboard('attest', '--repository', args.repository, '--commit', args.commit, '--output', str(out))
    print(proc.stdout.strip())

def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status').set_defaults(func=cmd_status)
    sub.add_parser('init-did').set_defaults(func=cmd_init)
    sub.add_parser('intro-dry-run').set_defaults(func=cmd_intro_dry)
    sub.add_parser('intro-publish').set_defaults(func=cmd_intro_publish)
    a = sub.add_parser('attest')
    a.add_argument('--repository', required=True)
    a.add_argument('--commit', required=True)
    a.set_defaults(func=cmd_attest)
    ns = p.parse_args()
    ns.func(ns)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
