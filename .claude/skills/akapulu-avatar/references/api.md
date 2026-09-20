# Akapulu REST, the parts this skill uses

Base `https://akapulu.com/api` · `Authorization: Bearer $AKAPULU_API_KEY` on every call.
**Every path ends in a slash.** Without one Akapulu answers 301, and a redirected POST arrives as
a GET, so the request looks like it worked and did nothing.

Branch on the `error_code` field, never on the English message.

## Knowledge base

```bash
POST /knowledge-bases/create/            {"name": "...", "description": "..."}   -> {id}
POST /knowledge-bases/<id>/documents/create/     multipart, NOT json
     -F name=...  -F description=...  -F file=@knowledge.txt
GET  /knowledge-bases/<id>/documents/     poll until every status is "completed"
```

The document is **UTF-8 text, 130 KB maximum**. Not a PDF. It arrives `pending` while Akapulu
chunks and embeds it, which takes about 15 to 20 seconds. A `rag` tool pointed at a knowledge
base whose document is still pending will find nothing, so always wait for `completed`.

## Scenario and hosted link

```bash
POST /scenarios/create/
{
  "name": "Harbour Lane front desk",
  "llm_model": "gpt-4.1-mini",
  "nodes_json": { ... },
  "hosted_links": [{"avatar_id": "<uuid>", "label": "Front desk", "stt_keywords": ["Clara"]}]
}
```

The response's `hosted_links[0].url` is a public `https://live.akapulu.com/session/<token>` page.
No SDK, no key in the browser, works on any website as a plain link.

- `stt_keywords` is capped at **5** per link. A sixth returns 400.
- On `POST /scenarios/update/`, `hosted_links` is a **full replace**: omit it to keep the links
  that exist, and `name` is required even when you are only changing `nodes_json`.
- `POST /scenarios/delete/ {"ids": [...]}` removes the scenario and its links.

## What has no API

- **Avatars.** `/avatars/`, `/catalog/` and `/avatars/list/` all return 404. Open
  https://akapulu.com/catalog, pick a face, copy the UUID from that avatar's page URL.
- **Secrets.** Created by hand at akapulu.com/secrets.
- **Testing mode.** Browser only, and it costs 0.25 credits per conversation.

## The hosted page

- `X-Frame-Options: DENY`, so an iframe or a lightbox renders an empty box. Link to it.
- `Cross-Origin-Opener-Policy: same-origin`, so a `target="_blank"` tab cannot talk back.
- It accepts a `redirect_url`, and sends the visitor there when the call ends.

## Cost

The free plan is 10 credits in total, a 3 minute cap on a call, and a watermark. Enough to build
this and test it properly. Say so before the first live call rather than after.
