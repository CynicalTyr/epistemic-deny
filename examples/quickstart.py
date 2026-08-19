#!/usr/bin/env python3
from epistemic import format_allowlist_block_result

print(
    format_allowlist_block_result(
        "cat /etc/shadow",
        reason="Not on the safe_prefixes allowlist.",
        alternative_tool="inspect_runtime_config",
        hard_block=True,
        identical_retry_count=2,
    )
)
