---
description: Build or query a code2graph knowledge graph
---

Invoke the `code2graph` skill immediately.

Pass the full `/code2graph` argument string through unchanged.
If no arguments were supplied, treat the target path as `.`.

Examples:
- `/code2graph`
- `/code2graph src --update`
- `/code2graph query "what connects auth to billing?"`

Do not answer from raw files before handing off to the `code2graph` skill.
