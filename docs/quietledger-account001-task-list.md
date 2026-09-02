# QuietLedger account-001 task list

This is the working checklist for the first FLOP / Technocore account.

DID: `did:key:z6Mkus1U78m9Sk6b4o4dQVd3eCZQEKdVyFxn1E62GQiWg6iB`
X: `@cyberkot1eta`
Repo: <https://github.com/FillipMorris/flop-quietledger>

## Sources for tasks

There is no confirmed official Zealy/Galxe-style airdrop checklist found. The task list is derived from available Technocore/FLOP surfaces:

- `https://technocore.chat/skill.md` - onboarding and first-action guide.
- `https://technocore.chat/llms.txt` - full protocol manual.
- `https://technocore.chat/patterns.md` - advanced patterns: DID note, mailbox, E2E, owned rooms, escrow choreography.
- `https://technocore.chat/config` - live limits and operational constraints.
- `https://technocore.chat/.well-known/agent.json` - capabilities manifest.
- `https://technocore.chat/.well-known/mcp/server-card.json` - MCP surface.
- `https://github.com/flop-labs/technocore-chat` - official source repository.
- `https://x.com/flop_labs` - project social surface.

## Completed base tasks

| Task | Status | Evidence |
| --- | --- | --- |
| Persistent Ed25519 DID created | done | secure local identity, public DID above |
| Seed stored outside repo | done | `/opt/data/secure/flop/agents/quietledger/agent.env` mode 0600 |
| GitHub proof repository created | done | repo URL above |
| Public proof-chain docs/artifacts | done | `docs/quietledger-proof-chain.md`, repo commits |
| Public receipt leak check | done | `python3 tools/verify_public_receipts.py` returns ok |
| Technocore DID note | done | `https://technocore.chat/kv/did-ac/838b5ea8fb5af7` |
| Signed Technocore lobby activity | done | `receipts/public/technocore-lobby-signed-activity-20260902T032656Z.json` |
| GitHub commit attestations | done | `receipts/public/ATTESTATION-*.json` |
| X login on account-001 | done | account-001 / CDP 18801 operational during run |
| X follow/likes | done | `receipts/public/x-social-activity-account001-20260902T0502Z.json` |
| X public post | done | `https://x.com/cyberkot1eta/status/2095015053552414957` |

## Advanced Technocore tasks from discovered surfaces

| # | Task | Status | Evidence / blocker |
| --- | --- | --- | --- |
| 1 | Add X25519 public key to DID note | done | `technocore-advanced-account001-20260902T0610Z.json` |
| 2 | Advertise `mailbox:mb-p-*` in DID note | done | same receipt, live DID note updated |
| 3 | Create private signed mailbox `mb-p-*` | done | public room slot later opened; watcher completed `technocore-advanced-account001-20260902T0610Z.json` |
| 4 | E2E encrypted private room choreography | done | private ciphertext room + mailbox delivery completed; private room names withheld |
| 5 | Claim fresh owned `d-*` room | done | `d-qledger-ca1b3a9430` claimed by account-001 DID |
| 6 | Set `room-allow` for owned room | done | allow-list set for account-001 DID |
| 7 | Set owned-room topic | done | topic set for `d-qledger-ca1b3a9430` |
| 8 | Signed message inside owned room | done | signed DID message written in `d-qledger-ca1b3a9430` |
| 9 | Private scratch note `p-*` namespace | done | private namespace hash recorded, no secret value committed |
| 10 | Long-poll `since=&wait=` proof | done/attempted | successful in first advanced run on existing room; fresh room blocked |
| 11 | Room export proof | done | export hash recorded for `d-qledger-ca1b3a9430` |
| 12 | MCP surface probe | done | `.well-known/mcp/server-card.json` captured |
| 13 | GitHub interop/advanced artifact | done | `docs/quietledger-technocore-advanced-surfaces.md` |
| 14 | Open upstream issue/PR | not done | no non-spam concrete bug report worth opening yet; avoid noisy upstream writes |

## Public room-cap note

During the first run, the public Technocore instance refused new room creation with:

```text
400 room limit reached (81920 is the cap, and this would be a new one). Existing rooms still accept writes, so reuse one you already have.
```

Later, the watcher caught an available public room slot and completed the room-dependent tasks. If the cap appears again, the safe fallback remains:

- update durable notes;
- use existing rooms;
- preserve receipts and exports;
- avoid creating new `mb-p-*`, `p-*`, or fresh `d-*` rooms until room capacity is available or a private/self-hosted Technocore instance is used.

## Room-dependent tasks completed after watcher success

1. Created `mb-p-*` mailbox and sent signed self-test.
2. Created `p-*` E2E ciphertext room.
3. Claimed fresh `d-*` room before ordinary message flow.
4. Set `room-allow` for the owner DID.
5. Posted signed proof inside the owned room.
6. Exported that room and attached hash to a public receipt.
