---
name: General issue
about: Track work, enhancements, bugs, chores, and policy proposals
title: '[ Type ] '
labels: []
assignees: []
---

## Summary

<!--
One paragraph or 2-3 bullets. The TL;DR of *what* is being proposed — reads
like a Slack message or a standup update. Punchy.
e.g. "Adopt a rolling latest-only support policy on master."
-->


## Background

<!--
The *why now*: current state, the problem, what changed externally to make
this matter. Free-form prose; can be a few paragraphs. Pain points and
specific file/line references welcome.
-->


## Options

<!--
Approaches considered, with trade-offs (cost, risk, blast radius). Mark the
preferred direction with **(proposed)** or 🟢 if you've landed on one.
Skip this section if there's only one realistic path.
-->


## TBDs

<!--
Open questions and decisions deferred until implementation. Things to
validate before starting the work, or while it's in flight.
-->


## Scope

<!--
What's in. Sub-bullets OK ("Hard requirements" vs "Stretch"). What's
explicitly *out* goes at the bottom in Out of Scope.
-->


## Tasks

### Code & config

<!--
Terraform, Python, shell, YAML, .tfvars templates, modules. The deployable
artifacts. Reference specific files / line numbers where useful.
-->

- [ ]

### Tests

<!--
tests/terraform/, tests/unit/, baseline regeneration, new fixtures, negative
cases that should now error.
-->

- [ ]

### Documentation

<!--
README, CLAUDE.md, CHANGELOG, documentation/, inline doc strings, the
TEMPLATE_terraform.tfvars table.
-->

- [ ]

### GitHub housekeeping

<!--
Labels, branch protection, rulesets, workflow tweaks, issue triage,
milestone bookkeeping, repo settings.
-->

- [ ]


## Sequencing

<!--
Multi-PR work? Plan the merge order here. Skip if this is a single-PR issue.
e.g.
  1. **PR 1 (small, low-risk)** — branch cut + branching_policy.md + label.
  2. **PR 2 (bulk simplification)** — all the deletions.
  3. **PR 3 (parallel)** — issue triage / relabeling.
-->

1. **PR 1** —
2. **PR 2** —


## Related Issues / PRs

<!--
Refs #..., Depends on #..., Blocks #..., Stacked on #...
GitHub auto-links these and shows backreferences on the target issues.
-->


## Out of Scope

<!--
Things this issue deliberately does *not* address. Link follow-up issues
if they exist; otherwise just name the deferred concern so future-you
knows it was intentional.
-->