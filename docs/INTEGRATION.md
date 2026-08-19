# Integration patterns

Return the packet **as the tool result string**. If it only hits syslog,
the model never sees it and will invent state.

This kernel has **no** MCP server. A harness (Cursor, Claude Desktop) must
map its sandbox deny onto the same packet *before* the next completion.

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
`brain._allowlist_identical_block_counts`. Pass the **same** object for
the whole tool loop or `STOP_RETRY` never fires.

## Harness / MCP host

Map native errors. Do not wrap the packet in “the tool failed because…”.
Put the packet first.

| Host event | Packet |
| ---------- | ------ |
| Command not in allowlist | `hard_block=True` |
| Sandbox denied | `verdict="denied"` |
| Unknown binary | `verdict="unknown"` |
| Needs human override | `verdict="restricted"` |

LangChain `wrap_tool_call` (Context7 `/websites/langchain_oss_python_langchain`)
turns exceptions into `ToolMessage(content="Tool error: Please check your
input and try again. ({e})")`. That copy is the bug. If you use that
middleware, return **this packet** as `ToolMessage.content`, not the
stock sentence.

MCP `CallToolResult.is_error` (GitHub
`modelcontextprotocol/python-sdk` `src/mcp-types/mcp_types/_types.py`)
is meant so the LLM can self-correct. Set `is_error=True` **and** put
the packet in `content`. Do not raise protocol-level `MCPError` for an
allowlist miss — the example `restricted()` tool in
`examples/stories/error_handling/server.py` hides the deny from the
model, which then interpolates.

Instructor `max_retries` reasks on Pydantic validation errors
(`docs/concepts/reask_validation.md`). Do **not** reask a hard-blocked
shell. Validation retry is for malformed JSON, not for permission denied.

## Capacity gate

`edge-capacity-gate` already emits `STATUS: CAPACITY_PRESSURE` in the
same family. Keep one shape for every “you may not do that.”

## Paste-ready policy

> Denies are data. Quote STATUS/VERDICT. Follow USE_INSTEAD. Never
> describe blocked files as empty or missing unless a legal tool showed
> that. If you see STOP_RETRY, answer in text only.
