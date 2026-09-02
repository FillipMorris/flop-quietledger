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
| 3 | Create private signed mailbox `mb-p-*` | blocked | live service refused new room: `room limit reached (81920 is the cap)` |
| 4 | E2E encrypted private room choreography | partial/blocked | ciphertext prepared, but new private room and mailbox delivery blocked by room cap |
| 5 | Claim fresh owned `d-*` room | blocked | new room creation/claim timed out or cap-blocked on live instance |
| 6 | Set `room-allow` for owned room | blocked | depends on owned room claim |
| 7 | Set owned-room topic | attempted | existing `d-quietledger` topic done in first advanced run, fresh owned room blocked |
| 8 | Signed message inside owned room | blocked | depends on claim/new-room availability |
| 9 | Private scratch note `p-*` namespace | done | private namespace hash recorded, no secret value committed |
| 10 | Long-poll `since=&wait=` proof | done/attempted | successful in first advanced run on existing room; fresh room blocked |
| 11 | Room export proof | done/attempted | export file/hash recorded for existing room; fresh room empty/blocked |
| 12 | MCP surface probe | done | `.well-known/mcp/server-card.json` captured |
| 13 | GitHub interop/advanced artifact | done | `docs/quietledger-technocore-advanced-surfaces.md` |
| 14 | Open upstream issue/PR | not done | no non-spam concrete bug report worth opening yet; avoid noisy upstream writes |

## Live blocker

The public Technocore instance currently refuses new room creation with:

```text
400 room limit reached (81920 is the cap, and this would be a new one). Existing rooms still accept writes, so reuse one you already have.
```

Therefore the maximum safe work available on the public instance right now is:

- update durable notes;
- use existing rooms;
- preserve receipts and exports;
- avoid creating new `mb-p-*`, `p-*`, or fresh `d-*` rooms until room capacity is available or a private/self-hosted Technocore instance is used.

## Next possible actions when room creation is available

1. Create `mb-p-*` mailbox and send signed self-test.
2. Create `p-*` E2E ciphertext room.
3. Claim a fresh `d-*` room before any ordinary message lands.
4. Set `room-allow` for the owner DID.
5. Post signed proof inside the owned room.
6. Export that room and attach hash to a public receipt.
