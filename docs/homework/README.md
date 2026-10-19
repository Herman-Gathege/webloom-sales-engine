# Homework

Every sprint has a folder. Open your own card, do that piece, and hand the line to the
next person.

## One branch, one line

We use **one shared branch per sprint**. No personal branches. Think of a car line: one
person adds a piece, checks it, pushes, and passes it on. This replaced separate branches
because nobody could tell which branch was safe to pull.

**Current sprint (Sprint 2) branch:** `sprint/2-lead-desk`

### Your turn

1. `git switch sprint/2-lead-desk && git pull` — start from what the last person pushed.
2. Run `docker compose up --build`. If the last hand-off is broken, say so before adding
   anything.
3. Do only what your card says.
4. Run the checks on your card until they pass.
5. `git add -A && git commit -m "<type>: <what you did>" && git push`
6. The first hand-off opens one PR from `sprint/2-lead-desk` to `main`. Every later hand-off
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
- [Sprint 2](sprint-2/README.md) — in progress.
