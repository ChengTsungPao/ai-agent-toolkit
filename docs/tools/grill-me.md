# grill-me

**Source:** [mattpocock/skills](https://github.com/mattpocock/skills) — MIT © Matt Pocock.
Vendored into `skills/grill-me/` + `skills/grilling/`.

## What it is

A relentless interview that sharpens a plan, design, or decision **before** any
code is written. You describe what you want, run `/grill-me`, and the agent maps
your idea as a decision tree and walks every branch — asking the highest-impact
unknowns first, one round at a time, with a recommended answer for each, never
moving on until a branch is resolved.

Needs no repo, writes no files, and the subject doesn't have to be code.

## How to use

```
/grill-me
```
(user-invoked only — `grill-me` has `disable-model-invocation: true`). It hands
off to the `grilling` skill, which runs the round-based interview loop. The
session ends when every branch is settled and you confirm shared understanding.

## Why vendored, not the plugin

The mattpocock plugin (`claude plugins install mattpocock-skills`) installs all
~25 of his skills and auto-updates. Here we only want `grill-me`, and the two
files are tiny and MIT — so they live in `skills/` as editable bundles. Pull
upstream changes by re-copying.

## Related (not installed)

`grill-with-docs` in the same repo is `grill-me` plus codebase-aware extras.
