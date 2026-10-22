# Project Phase Continuity Standard

This file defines the mandatory workflow for phase-based work in this repository. Every separate project repository should keep its own canonical state/checkpoint; changes here do not automatically update other repositories.

## Canonical records
- `docs/PHASE_STATE.md` (or an existing canonical registry such as `docs/PHASE_REGISTRY.md`): last verified phase, current in-progress phase, next incomplete phase, exact tested SHA, CI result, limitations and next action.
- `docs/PHASE_CHECKPOINTS.md` (or the existing phase ledger): chronological phase history and acceptance evidence.
- `docs/ROADMAP.md` or the existing roadmap/checkpoint file: ordered scope and dependencies.
- Prefer the repository's existing canonical files; do not create competing registers.

## Required before starting a phase
1. Read the canonical phase state/registry first.
2. Verify the active branch, current head SHA and newest GitHub Actions/checks. Do not assume an older green run validates newer code.
3. Read the relevant checkpoint and roadmap sections; search existing code, tests, migrations, API routes and workflows before changing anything.
4. If the phase already passed its exact-SHA acceptance gate, never repeat it unless a documented defect/new requirement requires revisiting it.
5. If a phase is in progress and CI is red, repair that same phase instead of skipping ahead.
6. Record the phase as IN_PROGRESS with exact scope, known prior work, acceptance criteria and dependencies before implementation.

## Required before marking complete
1. Add/update deterministic regression tests for expected behavior and failure/edge cases.
2. Run the project's required tests and full CI against the exact source/test SHA.
3. Mark COMPLETED only when that exact SHA's required checks pass and phase-specific live-data/deployment/device gates are also satisfied. A commit message, merged PR, file creation or syntax check alone is insufficient.
4. Update the canonical state, phase ledger and roadmap with the exact SHA, CI URL/result, test counts when available, known limitations, and the next incomplete phase.
5. Verify the final documentation commit and leave a clear cross-chat handoff.

## No skipping / no repetition
- The state file or canonical registry—not chat history—is the source of truth.
- Do not repeat completed phases or create a duplicate implementation; extend existing work when it already covers the requirement.
- Do not skip incomplete dependencies to work on later phases.
- If CI fails, keep the phase in progress, fix the issue, add a regression test when warranted and rerun on the resulting SHA.
- Keep external acceptance honest. Do not claim production data, device, microphone, network, migration, secret or interactive UI success from CI alone.
- For blocked phases, record the exact blocker and an actionable unblock condition. Do not bypass security or data-integrity gates to make a check green.

## New chat / cross-project handoff
- On a new chat, first read this repository's state/registry and latest CI before touching code.
- Every repository needs an independent copy/adoption of this policy and its own state record; updating one repository cannot automatically create memory or update files in other repositories.
- End each phase handoff with: last verified phase, current phase, next phase, exact evidence link(s) and remaining limitations.
