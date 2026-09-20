# Prompt 3 — the launcher button

Paste into your AI coding tool, in the folder with index.html, after you have copied your hosted link.

**Before you send it:** paste the hosted link you copied in step 2 into the marked line.
**Keep the trailing slash** — without it the server 301s and you pay a wasted round trip
on cellular before anything renders.

---

```
Add a button to the bottom right corner of the site you just built, where the
<!-- WIDGET SLOT --> comment is. When someone clicks it, it takes them to this link, in the
same tab:

  https://live.akapulu.com/session/PASTE_YOUR_TOKEN_HERE/

Do not open it in an iframe or a popup. It will not work that way, it has to be a plain link.
Make the button look like it belongs on the site, with a small label that says "Talk to our
receptionist". Keep the whole thing in one block in index.html so I can copy it onto another
site later.
```

---

## If Astra's version is worse than the reference

`widget/launcher.html` in this repo is a known-good implementation. Paste that in place of the
`<!-- WIDGET SLOT -->` comment instead, and change the one `href`.

## Why a link and not a popup — VERIFIED, not assumed

Headers on a live hosted page, checked Sep 15 2026:

```
x-frame-options: DENY
cross-origin-opener-policy: same-origin
```

- **`X-Frame-Options: DENY`** means an iframe, modal or lightbox renders as a blank box. Not a
  design preference. A server header. Navigation is the only mechanism available.
- **`Cross-Origin-Opener-Policy: same-origin`** severs `window.opener`, so a `target="_blank"`
  tab cannot talk back to your page at all — you could not detect "call ended" even if you tried.
- The hosted page supports **`redirect_url`** and does `window.location.href = redirectUrl` the
  moment the call ends. Point it at your landing page and the visitor returns automatically,
  which is the thing a new tab was supposed to solve.
- No `beforeunload` handler is set, so the browser Back button returns instantly with no
  "Leave site?" dialog.
