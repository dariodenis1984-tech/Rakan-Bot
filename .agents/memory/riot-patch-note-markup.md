---
name: Riot patch-note markup
description: Non-obvious parsing behavior of the official Wild Rift patch-notes index.
---

The official Wild Rift patch-notes page exposes a clean patch title in each card's `aria-label`, while the visible anchor text concatenates the category, publish timestamp, title, and summary without separators.

**Why:** Matching only visible card text can produce empty matches or titles that accidentally include the beginning of the summary.

**How to apply:** Prefer the card's `aria-label` when extracting patch titles; use a version-shaped fallback only when that metadata is unavailable.