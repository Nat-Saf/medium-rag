---
name: session-resume
description: Update docs/RESUME.md with a summary of the work done since the last
  git commit, so the project can be resumed from another machine or after a break.
  Invoke this as the FIRST step before any git commit (before staging/committing).
---

# Session resume updater

Keep `docs/RESUME.md` as a living, single-screen "pick up here" document. It is the
ONLY portable handoff state — it is committed to git, so it travels to every clone.
(The agent memory in `~/.claude` does NOT sync across machines; never rely on it for
resume.) Run this BEFORE each commit so the committed snapshot is always current.

## When to run
- Right before any `git commit` / push, as the first step of the commit ritual.
- Whenever the user asks to "save resume state" / "update RESUME".

## Procedure
1. **Find what changed since the last commit:**
   - `git log -1 --format='%h %s'` — the baseline commit.
   - `git diff --stat HEAD` and `git status --short` — staged, unstaged, and
     untracked changes since that commit.
   - Skim the conversation since the last commit for *why* those changes were made
     and any decisions/blockers that aren't obvious from the diff.
2. **Rewrite `docs/RESUME.md`** so it reflects the CURRENT state. Keep it short
   (about one screen). Include these sections:
   - **Last updated** — today's date (ask or use the known current date; do not
     guess relative dates).
   - **Status / current phase** — the build phase (0–6 per CLAUDE.md) and whether
     it is in progress or done.
   - **Since last commit** — bullet list of what changed and why, in plain English.
   - **Next step** — the single concrete command/action to resume with.
   - **Open blockers / decisions** — env quirks, budget spent so far, anything that
     would trip up a fresh machine.
   - **Constraints** — carry forward the hard limits (chunk_size ≤ 1024,
     overlap ≤ 0.3, top_k ≤ 30; $5 budget; batch embeds; never commit secrets/CSV;
     models are the `NBUECSE-*` namespace, NOT the PDF's `ZYRANGG-*` placeholder).
3. **Stage it** so it lands in the SAME commit: `git add docs/RESUME.md`.
4. Hand control back to the normal commit flow (the model writes the commit message
   and commits as usual).

## Notes
- This skill only updates and stages `docs/RESUME.md`; it does not create the commit
  itself.
- Do not put secrets, keys, or dataset rows in RESUME.md — it is committed to a
  public repo.
