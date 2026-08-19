# Advanced: why LLMs invent config after “permission denied”

Search terms: *LLM hallucinates after permission denied*, *agent allowlist
bypass python -c*, *tool result epistemic packet*, *stop retry identical
command*.

---

## 1. The incident class

An operator asks whether a feature flag is on. The allowlist blocks
`grep` of `.env`. The model reports: **“the flag is unset.”**

Nothing read the file. The model treated a deny as negative evidence.
That is not a “dumb model”; it is a **missing compiler error**. Humans
get `error: cannot open`. Models get a blob that looks like any other
tool chatter.

---

## 2. What the packet is for (not the human)

`STATUS` / `WHY` / `USE_INSTEAD` / `RETRY_RULE` / `AGENT_RULE` /
`EPISTEMIC_RULE` are in-band training. If you omit `USE_INSTEAD`, the
model retries `python -c`, then `/usr/bin/python3 -c`.
`identical_retry_count >= 2` + `STOP_RETRY` is the circuit breaker.

Normalize commands before hashing if you need variants to count as one
(this library hashes the raw `cmd`; your dispatcher can canonicalize).

---

## 3. Real-world: version checks

Agents love `python -c "import foo; print(foo.__version__)"`. Hard-block
that and append `NEXT_LEGAL_MOVES: pip show`. The doctrine in
`epistemic.py` exists because “what version is installed?” is the most
common innocent loop that still violates allowlists.

---

## 4. Real-world: capacity and coherence

Capacity pressure and iteration clamps should use the **same shape**.
One family of packets is easier to teach a model than five ad-hoc
strings. See `edge-capacity-gate` and `agent-coherence-clamp`.

---

## 5. Comparison

| Approach | Result |
| -------- | ------ |
| Raise `PermissionError` | Harness may stringify poorly; model invents |
| Return `"blocked"` | Too small; no next move |
| This packet | Status + next legal move + stop-retry |

---

## 6. Measuring use

Count turns where STATUS appeared in the tool stream vs turns where the
model asserted file contents after a deny (those should fall).

---

## 7. Related reading

[`START_HERE.md`](../START_HERE.md) · `agent-review-envelope` docs/ADVANCED.md
(queues, not denies).

## Hidden dynamics (short)

- Pattern: Denies are data. A blocked tool must return STATUS/WHY/USE_INSTEAD, not “permission denied.”
- Loop: Deny without USE_INSTEAD → python -c → /usr/bin/python3 -c. identical_retry ≥ 2 → STOP_RETRY is the breaker.
- Incentive: Models are rewarded for answering. After a deny they invent negative evidence (“flag unset”).
- Leverage: Put the packet in the *tool result*, not syslog. If the model never sees it, it will lie.
- Harness: Map the harness sandbox deny to this packet *before* the next completion. Do not summarize it first.
- Custom AI: In your dispatcher, return finalize_hard_allowlist_block(...) as the tool string. If force_text, tools=[].

