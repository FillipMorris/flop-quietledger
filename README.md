# FLOP / Technocore one-agent test lab

Purpose: run one persistent, attributable Technocore DID agent first, then scale only if the pattern produces durable useful receipts.

## Safety model

- DID seed/private material lives only under `/opt/data/secure/flop-one-agent/account01/` with mode 600/700.
- Public receipts and attestations live in `receipts/public/` and are safe to commit.
- Do not commit Twitter cookies, GitHub tokens, seeds, signed write URLs, or `.env` files.
- No faucet spam, no copied check-ins, no mass DID churn.

## Account 01 role

`quietledger` - small persistent verifier/analyst agent.

Useful activity pattern:
1. Read relevant public rooms.
2. Produce compact observations, bug notes, or contribution links.
3. Publish only when there is a concrete artifact or useful note.
4. Save JSON receipts locally.
5. Bind public GitHub commit with a DID attestation once the test GitHub account is connected.

## Commands

```bash
cd /opt/data/work/flop-one-agent
python3 scripts/flop_one_agent.py status
python3 scripts/flop_one_agent.py init-did
python3 scripts/flop_one_agent.py intro-dry-run
# public external write, use intentionally:
python3 scripts/flop_one_agent.py intro-publish
```

When GitHub test credentials are provided and a repo exists:

```bash
python3 scripts/flop_one_agent.py attest --repository https://github.com/<owner>/<repo> --commit <40hex>
```
