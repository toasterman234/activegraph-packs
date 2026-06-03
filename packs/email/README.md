# Email Pack v0.1

Translates inbound emails into channel-neutral CommMessage objects and handles the
draft → approval → send flow with configurable external write gating.

## Purpose

Email Pack is the adapter between email (webhook / IMAP) and the Communication Pack's
semantic layer. It handles email threading (In-Reply-To / References), deduplication
by RFC 2822 Message-ID, draft formatting, and a safety gate for external outbound sends.

> SMTP/IMAP connection is out of scope — production adapters inject `EmailMessage`
> objects via tool calls or webhooks. The pack provides the structure; transport is external.

## Object Types

| Type | Description |
|---|---|
| `email_message` | Raw inbound email (headers, MIME bodies, threading refs) |
| `email_thread` | Email thread grouping messages by In-Reply-To / References |
| `email_draft` | Formatted outbound draft pending approval and delivery |

## Relation Types

| Relation | Source → Target | Description |
|---|---|---|
| `email_thread_contains` | email_thread → email_message | Thread contains message |
| `draft_responds_to` | email_draft → email_message | Draft replies to email |
| `draft_from_candidate` | email_draft → comm_response_candidate | Draft from candidate |
| `email_linked_to_comm_thread` | email_thread → comm_thread | EmailThread ↔ CommThread |

## Behavior Map

```
email_message.created
  → email_ingester
      dedup: skip if message_id already in _EMAIL_MESSAGE_REGISTRY
      creates/updates: email_thread (threaded by In-Reply-To / thread_id)
      creates: source(kind=email, channel=email)
      creates: comm_message(channel=email, direction=inbound)
      relations: email_thread_contains, derived_from_source
      hook: source.created → Identity Pack principal_resolver (if loaded)

comm_response_candidate.created [channel=email]
  → reply_drafter
      reads: original comm_message for subject + sender (to_addrs)
      creates: email_draft(subject="Re: ...", body=content+signature)
      relations: draft_from_candidate

email_draft.created
  → send_approver
      checks: to_addrs vs owner_email_addresses + trusted_domains
      if external AND require_approval_for_external=True:
        creates: action(kind=approval_request, risk_class=high)
        draft.status stays "draft" (awaiting owner approval)
      else (internal/trusted or approval disabled):
        patches: email_draft.status = "approved"
        patches: comm_response_candidate.status = "approved"
        → triggers response_dispatcher (Communication Pack)
```

## Approval Gate

```
External send (default policy):
  email_draft.created (to_addrs contains external address)
    → send_approver
        → action(kind=approval_request, risk_class=high)
  Owner reviews → approves → patches email_draft.status = "approved"

Internal send (owner ↔ owner):
  email_draft.created (to_addrs all in owner_email_addresses or trusted_domains)
    → send_approver → auto-approves (no action created)
```

## Settings

```python
EmailSettings(
    require_approval_for_external=True,           # Gate on external sends
    owner_email_addresses=["alice@example.com"],  # Internal addresses
    trusted_domains=["mycompany.com"],            # Trusted domains (bypass gate)
    auto_create_threads=True,                     # Auto-create EmailThread
    draft_signature="Best,\nAlice",               # Appended to all drafts
    max_body_length=50_000,                       # Body truncation limit
    default_reply_format="plain_text",            # "plain_text" or "html"
)
```

## Usage

```python
from activegraph import Runtime, Graph
from packs.core import pack as core_pack
from packs.communication import pack as comm_pack
from packs.email import pack as email_pack, EmailSettings
from packs.email.tools import ingest_email_fn, create_email_response_fn

g = Graph()
rt = Runtime(g)
rt.load_pack(core_pack)
rt.load_pack(comm_pack)
rt.load_pack(email_pack, settings=EmailSettings(
    owner_email_addresses=["alice@example.com"],
    require_approval_for_external=True,
))

# Receive inbound email
ingest_email_fn(g,
    message_id="<msg001@mail.example.com>",
    from_addr="founder@startup.com",
    to_addrs=["alice@example.com"],
    subject="Investment interest",
    body_text="Hi Alice, interested in a term sheet discussion.",
)
rt.run_until_idle()
# → Source + CommMessage + EmailThread in graph
# → CommIntent from intent_detector
# → Principal from Identity Pack (if loaded)

# Draft a reply
comm_msg_id = list(g.objects(type="comm_message"))[0].id
create_email_response_fn(g,
    comm_message_id=comm_msg_id,
    content="Thank you for reaching out! I'd love to schedule a call.",
)
rt.run_until_idle()
# → EmailDraft created
# → Action(kind=approval_request, risk_class=high) created (external send)
```

## Composes With

- **Core Pack** (required): source creation
- **Communication Pack** (required): CommMessage, CommThread, intent_detector, thread_tracker
- **Identity Pack** (optional): source.sender_ref → principal_resolver creates Principal
- **Tool Gateway Pack** (optional): approval_request Action flows through Tool Gateway

## Notes

- `clear_email_registry()` and `clear_thread_registry()` between test fixtures
- Dedup is by RFC 2822 Message-ID (handles webhook retries)
- `email_ingester` sets `metadata.thread_id_hint` so `thread_tracker` can co-locate CommThread
- `reply_drafter` strips `Re:`/`Fwd:` prefixes from subject for consistent threading
