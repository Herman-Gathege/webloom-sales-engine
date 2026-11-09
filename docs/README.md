# Documentation

New to Wadi or returning after a break? Start with the five-minute orientation:

1. Open the [visual workflow](workflow.html) for the whole journey in one view.
2. Read the [workflow description](workflow-description.md) for inputs, human decisions and
   stop conditions.
3. Use the [full Wadi guide](full-wadi-documentation.md) for current status, architecture,
   gaps and the road ahead.

Then open the document that matches what you are about to do.

| If you want to know… | Read |
|---|---|
| what we are building, and what is out of scope | [scope spec](superpowers/specs/2026-10-08-webloom-sales-engine-scope.md) |
| where Wadi has been, where it is and where it is going | [full Wadi guide](full-wadi-documentation.md) |
| one lead's journey, with human and automation boundaries | [workflow description](workflow-description.md) |
| the whole plan: nine sprints, and who leads each | [sprint plan](delivery/sprint-plan.md) |
| the current sprint contract and ownership | [Sprint 5 campaigns and drafts](delivery/sprint-5-campaigns-drafts.md) |
| who implements and who reviews Sprint 5 | [Sprint 5 homework](homework/sprint-5/README.md) |
| the closed Sprint 4 catalogue and its accepted deviations | [Sprint 4 offers and templates](delivery/sprint-4-offers-templates.md) · [exit review](homework/sprint-4/status.md) |
| the CSV-to-outreach compliance flow, statuses, filters, and current boundary | [Sprint 3 solidification](delivery/sprint-3-solidification.md) |
| how the last four sprints went | [Sprint 4](homework/sprint-4/status.md) · [Sprint 3](homework/sprint-3/status.md) · [Sprint 2](homework/sprint-2/status.md) · [Sprint 1](homework/sprint-1/status.md) |
| deep detail on every piece of work | [sprint detail](delivery/sprint-detail.md) — reference only |
| how we branch, review, and merge | [how we work](team/how-we-work.md) |
| what we verified about FikaTu | [FikaTu integration notes](research/2026-10-08-fikatu-integration-notes.md) |
| the exact Lead shape the API and UI agree on | [Sprint 1 lead contract](delivery/sprint-1-lead-contract.md) |
| the shape of the CSV import, so the upload screen can call it | [Sprint 2 import contract](delivery/sprint-2-import-contract.md) |
| what the importer does, and why it is built that way | [Sprint 2 importer notes](delivery/sprint-2-import-notes.md) |
| what the first lead list actually contains | [lead list audit](research/2026-10-08-lead-list-audit.md) |
| the compliance boundary and practical outreach workflow | [compliance foundation](compliance/README.md) · [outreach SOP](compliance/outreach-sop.md) |
| what the safeguard implementation covers, and what remains for sending | [compliance implementation notes](compliance/implementation-notes.md) |
| why a decision was made | [decision records](decisions/) |

## Folders

```
docs/
├── workflow.html             public visual orientation and app landing page
├── workflow-description.md   the canonical stage-by-stage journey
├── full-wadi-documentation.md  the complete project snapshot
├── superpowers/specs/   the scope spec — the gate
├── delivery/            the sprint plan, and the detailed backlog behind it
├── homework/sprint-1/   the finished first sprint: its cards, and its record
├── homework/sprint-2/   the second sprint: its cards, and its exit review
├── homework/sprint-3/   the completed authentication/compliance sprint
├── homework/sprint-4/   the completed commercial-catalogue sprint and exit review
├── homework/sprint-5/   Herman implementation plus Mark, Sharon and Anne review cards
├── team/                how we work
├── research/            verified findings: FikaTu, the lead list
├── compliance/          legal boundaries, operating rules, implementation status
└── decisions/           ADRs for decisions that are expensive to reverse
```
