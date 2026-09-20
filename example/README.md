# Example: Harbour Lane Dental

These two files were produced by the skill from a dental practice website that GPT-6 Astra built
from a single prompt. Nothing here was written by hand.

- `knowledge.txt` — 3.7 KB of the site's own content: services, hours, parking, the FAQ answers,
  and the practice's stated position on costs
- `scenario.json` — her persona and her two tools. The `knowledge_base_id` is a placeholder;
  put your own there after you create the knowledge base

Two things to notice, because they are the point of the whole repo:

**She has no prices, and she does not invent any.** The site deliberately does not publish
prices. Ask her what whitening costs and she says the team explains the options and the costs
before any treatment, then offers to note your question down.

**Not one fact lives in her persona.** Every answer is looked up. That is why editing
`knowledge.txt` changes what she says.

## The avatar used in the video

`1f777f64-3758-4a7d-9cbc-c64ae654f7d1` — Clara, from the public catalog.

The skill will always ask you to pick your own, because there is no API that lists avatars and
because you should see the faces before you choose one. If you just want it to work, hand it
this one.
