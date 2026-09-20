# Scenario JSON: the shape and every rule

Source: https://docs.akapulu.com/guides/scenarios/using-json
`scripts/validate_scenario.py` enforces all of it. Run it rather than reading this twice.

## Shape

```json
{
  "initial_node": "desk",
  "role_instruction": "Who she is and how she speaks. Applies to the whole conversation.",
  "nodes": {
    "desk": {
      "task_instruction": "What to do in this node.",
      "functions": [
        {"name": "look_up_practice_info", "description": "When to call this.",
         "type": "rag", "knowledge_base_id": "<KB_ID>"},
        {"name": "look_at_camera", "description": "When to call this.", "type": "vision"}
      ]
    }
  }
}
```

`nodes` is an **object keyed by node name**. The key is the name, so there is no `name` field
inside the node.

## Top level

- `initial_node` required, must match a node key
- `role_instruction` optional, non-empty if present, 4,000 characters max
- `nodes` required, non-empty object
- No other top-level keys
- The whole thing is 20,000 characters max

## Node

Allowed keys: `task_instruction`, `functions`, `respond_immediately`,
`end_after_bot_response`, `require_function_call`.

- `task_instruction` required, non-empty, 4,000 max
- the three booleans are optional and must be real booleans
- `require_function_call: true` needs at least one function
- `functions`, if present, is a list

## Function

Allowed keys: `name`, `description`, `type`, `transition_to`, `allowed_next_nodes`,
`endpoint_id`, `knowledge_base_id`, `parameters`, `require_reason`, `filler_speech`.

- `name` required, unique within the node, letters/numbers/underscore/hyphen only, no stray spaces
- `description` required. It is the only thing the model reads when deciding whether to call the
  tool, so write **when to use it**
- `type` is one of `transition`, `http`, `rag`, `vision`, and defaults to `transition`
- `transition_to` on any type moves to that node after the call; it must name a real node
- `filler_speech: true` adds a spoken filler argument while the tool runs

| type | must also carry |
|---|---|
| `transition` | `transition_to` |
| `http` | `endpoint_id`, and either `transition_to` or `allowed_next_nodes`, never both |
| `rag` | `knowledge_base_id` |
| `vision` | nothing |

`allowed_next_nodes` is http-only: a non-empty list of unique, existing node names, from which
Akapulu picks based on the endpoint's response. `require_reason` is transition-only.

## Writing a persona that sounds like a person

Everything she writes is spoken aloud, so the instruction has to forbid what looks fine on a page:

- plain text only, no markdown, no asterisks, no bullet points, no numbered lists
- one or two short spoken sentences at a time
- one question at a time, then wait
- acknowledge what the caller said before moving on
- stop talking when interrupted
- offer one option and ask if it works, rather than reading a menu

Then say what she does about things she does not know: call the knowledge tool, and if the answer
is not in there, say so plainly instead of inventing one.
