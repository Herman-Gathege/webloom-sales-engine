# How we work

Four people, part-time, alongside demanding day jobs. So these rules are short on purpose.
If a rule stops helping, propose changing it — don't quietly ignore it.

## The one rule that governs the rest

**The human team agrees the contract/decision. AI helps implement it. A human reviews the
result.** Nobody merges a decision an agent made for them.

## Branching

- `main` is the latest integrated working state. It should always run.
- One shared branch per sprint: `sprint/<number>-<short-name>`. No personal branches.
- Everyone adds to that branch in turn. The branch lives for the sprint, then it closes.
- Nothing is pushed straight to `main`. Ever.

The steps, and how to hand off, are in [`docs/homework/README.md`](../homework/README.md).

## Pull requests

- One sprint PR from the sprint branch to `main`. The first hand-off opens it; every later
  hand-off pushes to the same branch and updates it.
- Keep each hand-off small. If the description needs paragraphs, it's too big.
- Description answers three things: what it does, how to run/demo it, what to check.
- Open a draft PR as soon as the piece is coherent. Don't hold work back until it's perfect.
- Keep real changes under ~400 lines. Past that, split it.

## Review

- One approval to merge; two for anything touching auth, sending, the database schema, or the
  FikaTu seam — and Mark is one of them.
- The reviewer checks: does it do what the card said, does it run, is anything risky or
  over-built?
- Review within a working day, even if the answer is "this needs work". A PR waiting on you
  blocks the whole team.
- The author answers or fixes. The coordinator merges the sprint PR when the sprint is done.
  If the coordinator wrote the last piece, someone else merges.

## Integration

- One person works on the sprint branch at a time. When their piece is green, the coordinator
  reviews it against the card.
- The next person pulls the same sprint branch and adds their piece.
- If `main` moved, merge `origin/main` into the sprint branch, re-run the checks, and push
  before handing off. Never leave a conflict for the next person.
- The sprint PR merges to `main` when the sprint is done. Run the sprint demo first. If it
  does not run, fixing it is the next thing anyone does.

## What "done" means

A piece is done when someone other than the author can:

1. pull the sprint branch (or `main` after the sprint merges) and start it from a clean state,
2. run that piece's demo and see it work,
3. see its tests pass,
4. undo it where it matters (migrations are reversible).

Writing the code is not done.

## Using AI / Codex

- Agree the contract as humans first, then let AI implement it.
- AI output is a draft. A human reviews it before merge. Always.
- One writer per file. When several agents or people work at once, agree who owns which
  files first.
- Every AI-assisted PR still names the human who is accountable for it.
- If an agent would have to guess a requirement, it stops and asks instead of inventing one.

## Keeping tasks small

- A piece should fit in one normal workday. Bigger than that, cut it in half.
- Prefer a thin working slice over a complete layer.
- No unnecessary abstraction. Build it for now, not for an imagined later.
- Stuck or unsure? Ask early — not after a week of work.

## Disagreements

- Argue the decision, not the person, and write the options down.
- Prefer evidence: what do the demo, the test, or the data actually show?
- Small and reversible: decide in the PR and move on.
- Expensive to reverse: bring it to the team, then record the choice as an ADR in
  `docs/decisions/`.
- If you still disagree, the owner of that area decides and notes the dissent. We move, and
  we can revisit it next sprint.

## What we change as we go

At the end of every sprint we write down one thing to keep and one thing to change, and that
note travels into the next sprint's homework.
