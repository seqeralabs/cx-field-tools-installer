---
name: General issue
about: Track work, enhancements, bugs, chores, and policy proposals
title: '[ Type ] '
labels: []
assignees: []
---

<!--
Canonical labels — pick from this list; don't invent new ones.

  Type (what kind of work):
    bug             — Something isn't working
    enhancement     — New feature or request
    refactor        — Restructure without changing behavior
    tech-debt       — Cleanup of historical accretion
    chore           — Misc cleanup not better described above
    deprecation     — Removing or warning about deprecated behavior
    breaking-change — Behavior-changing edit users will notice
    documentation   — Docs / README / CHANGELOG / inline docstrings

  Domain (what part of the system):
    validation      — Variable validation / configuration checking
    testing         — Test infrastructure / fixtures / regression
    dx              — Developer experience improvements
    ux              — End-user / deployer experience improvements

  Triage / lifecycle:
    question        — Further information requested
    help wanted     — Extra attention needed
    duplicate / invalid / wontfix — lifecycle states

  Release milestones (apply if targeted):
    v1.8 Release    — Targeted for 1.8
    v2 Release      — Targeted for v2
    review_for_26.1 — Linked to Platform v26.1 review
-->


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
Approaches considered, with trade-offs (cost, risk, blast radius).

Use `### Recommended` for the proposed direction and `### Alternatives` for
paths considered and rejected (with a one-line "Rejected because:" so future
readers see the reasoning without re-running the analysis).

Skip this whole section if there's only one realistic path.
-->

### Recommended

<!--
The proposed approach. Describe the architecture, sketch implementation,
and list tradeoffs (Pros / Cons or "accepted tradeoffs").
-->


### Alternatives

<!--
Other paths considered. For each: brief description, pros, cons, and an
explicit "Rejected because: …" line.

e.g.
  **Switch to library X**
  Brief description.
  Pros: …
  Cons: …
  Rejected because: …
-->


## TBDs

<!--
Open questions and decisions deferred until implementation. Things to
validate before starting the work, or while it's in flight.
-->


## Scope

### In Scope
<!--
What's in. Sub-bullets OK ("Hard requirements" vs "Stretch").
-->

### Out of Scope
<!--
Things this issue deliberately does *not* address. Link follow-up issues
if they exist; otherwise just name the deferred concern so future-you
knows it was intentional.
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
