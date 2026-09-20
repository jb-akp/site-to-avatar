# Three constraints that are not in the public docs

Each one was found by having a request rejected.

## 1. `nodes` is an object, not a list

```json
✗ "nodes": [ {"name": "desk", "task_instruction": "..."} ]
     -> {"error": "nodes_json.nodes must be a JSON object"}
✓ "nodes": { "desk": {"task_instruction": "..."} }
```

The node's name is the key. Do not also put a `name` field inside the object. This is the mistake
a language model makes most often here, because a list of named things is the more natural shape.

## 2. An `{{llm.*}}` token may contain exactly one period

The check counts periods across the **whole token, description included**. A description written
as a sentence fails:

```
✗ {{llm.question:The user's question, restated. Astra cannot see this conversation.}}
     -> {"error": "Invalid template variable format"}
✓ {{llm.question:The users question restated in full and self-contained, since Astra cannot see it}}
```

Commas are fine. Full stops are not. Write descriptions as one comma-spliced clause.

## 3. Endpoint body values must be strings

No booleans, no numbers, no nested objects.

```
✗ "body": {"model": "gpt-5", "background": true, "reasoning": {"effort": "low"}}
     -> {"error": "Function ... body values must be strings"}
```

If a downstream API needs real types, put a small proxy in front of it that takes flat strings and
builds the real request.

## Also worth knowing

- `GET /scenarios/` and `GET /endpoints/` exist. `GET /conversations/` does not.
- An `http` function with no `transition_to` fires without changing nodes.
- Endpoint `name` is unique per user, which makes find-by-name a safe idempotency key.
- The free plan is limited to Basic models. `gpt-4.1-mini` is the documented default, and
  full-size models are rejected on a free account.
