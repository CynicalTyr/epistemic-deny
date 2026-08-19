# Integration patterns

Return the packet **as the tool result string**. If it only hits syslog,
the model never sees it and will invent state.

## Dispatcher (local agent)

```python
from epistemic import block_guidance_from_actions, finalize_hard_allowlist_block

if not allowlist_ok(cmd):
    text, force_text = finalize_hard_allowlist_block(
        brain,
        cmd,
        guidance=block_guidance_from_actions(actions),
    )
    append_tool_result(text)
    if force_text:
        disable_tools_for_rest_of_turn()
    continue
```

`brain` is any object; the counter is stored on
`brain._allowlist_identical_block_counts`.

## Harness / MCP host

Map native errors:

| Host event | Packet |
| ---------- | ------ |
| Command not in allowlist | `hard_block=True` |
| Sandbox denied | `verdict="denied"` |
| Unknown binary | `verdict="unknown"` |
| Needs human override | `verdict="restricted"` |

Do not wrap the packet in “the tool failed because…”. Put the packet
first.

## Capacity gate

`edge-capacity-gate` already emits `STATUS: CAPACITY_PRESSURE` in the
same family. Keep one shape for every “you may not do that.”

## Paste-ready policy

> Denies are data. Quote STATUS/VERDICT. Follow USE_INSTEAD. Never
> describe blocked files as empty or missing unless a legal tool showed
> that.
