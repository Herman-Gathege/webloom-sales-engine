# Homework

Every sprint has a folder. Open your own card, do that piece, and hand the line to the
next person.

## Shared Wadi orientation

Spend five minutes here before a sprint review:

1. Open the [visual Wadi workflow](../workflow.html).
2. Read the [stage-by-stage workflow](../workflow-description.md).
3. Skim the [full Wadi guide](../full-wadi-documentation.md) for status, gaps and roadmap.

This is the shared map. Individual homework should send each person back to the part that
affects their review, not ask them to reread everything.

## One branch, one line

We use **one shared branch per sprint**. No personal branches. Think of a car line: one
person adds a piece, checks it, pushes, and passes it on. This replaced separate branches
because nobody could tell which branch was safe to pull.

**Sprint 4 branch:** `sprint/4-offers-templates` — merged and closed.

**Current sprint branch:** `sprint/5-campaigns-drafts`. Herman is the sole implementation owner;
Mark, Sharon and Anne review without opening parallel implementation branches.

### Your turn

1. `git switch sprint/5-campaigns-drafts && git pull` for Sprint 5. Sprint 4 is closed; use its
   [exit review](sprint-4/status.md) for evidence rather than re-running the acceptance guide.
2. Run `docker compose up --build`. If the last hand-off is broken, say so before adding
   anything.
3. Do only what your card says.
4. Run the checks on your card until they pass.
5. `git add -A && git commit -m "<type>: <what you did>" && git push`
6. The first hand-off will open one PR from the new sprint branch to `main`. Every later hand-off
   pushes to the same branch and updates that PR. Post in the group:
   **"pushed, green — your turn, <name>."**

### The merge

- The coordinator reviews each hand-off against the card's **Done means**.
- The next person pulls the same branch and repeats.
- The sprint PR merges to `main` when the sprint is done. If the coordinator wrote the last
  piece, someone else merges.
- If the coordinator merges mid-sprint, the next person pulls `main` and cuts the sprint
  branch again from it. If he has not merged, they pull the branch and carry on.

### If `main` moved

```bash
git fetch origin
git merge origin/main
```

Re-run the checks, push, then hand off. Never leave a conflict for the next person.

### Three rules

- **One person on the branch at a time.** Blocked? Say so in the group. Do not open a
  second branch.
- **Never push to `main`.** The PR is the only way in.
- **One branch per sprint.** It stays open until the sprint is done, then it closes.

### Success looks like

- `docker compose up --build` works from the branch.
- Your card's **Done means** is true.
- The sprint pull request is green and ready to merge.
- The next person can pull and start without asking you anything.

## Sprints

- [Sprint 1](sprint-1/README.md) — finished.
- [Sprint 2](sprint-2/README.md) — finished; exit review in [status.md](sprint-2/status.md).
- [Sprint 3](sprint-3/status.md) — finished; authentication and compliance boundary.
- [Sprint 4](sprint-4/status.md) — closed with accepted deviations; catalogue shipped.
- [Sprint 5](sprint-5/README.md) — Herman implements alone; Mark, Sharon and Anne review.
