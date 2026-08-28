# Source

`grill-me` (and its delegate `grilling`) are vendored from
**[mattpocock/skills](https://github.com/mattpocock/skills)** — MIT © Matt Pocock —
`skills/productivity/grill-me/` and `skills/productivity/grilling/`.

Vendored (not plugin-installed) on purpose: they're tiny, MIT, and meant to be
adapted. To pull upstream changes, re-copy from that repo.

`/grill-me` is user-invoked only (`disable-model-invocation: true`); it hands off
to the `grilling` skill, which does the actual relentless-interview loop. Keep
both bundles together.
