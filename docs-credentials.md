# Credential intake for account01

Send or place credentials only when ready. I will not print them back.

## GitHub test account

Preferred: create a fine-grained or classic PAT with repo access for the test repo.
I will store the gh session under:

`/opt/data/secure/flop-one-agent/account01/gh/`

Validation command:

```bash
printf '%s' '<GITHUB_PAT>' | /opt/data/work/flop-one-agent/scripts/connect_github_test.sh
```

## X/Twitter test account

Needed fields, stored only in secure env or isolated browser profile:

```bash
TWITTER_USERNAME=
TWITTER_PASSWORD=
TWITTER_EMAIL_OR_PHONE=
TWITTER_2FA_SECRET=
```

Planned binding after login: one human-readable profile/bio/link or post that references the DID and GitHub repo. No automated mass posting.
