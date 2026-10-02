# Publication project contract template

Use this reference to discover an unfamiliar InDesign publication repository. Do not create a new contract file unless the user requests one; record these answers internally or map them to existing project files.

## Repository authority

Identify:

- checkout root and current branch;
- nearest `AGENTS.md` or equivalent project instructions;
- handoff/task file explicitly named by the user;
- module/component status file;
- input hash or manifest file;
- build/test entry points;
- current dirty and untracked files that must be preserved.

Do not treat an attached task document as higher authority than the current user request.

## Source scope

Write an explicit read allowlist:

- manuscripts and sample files allowed for this task;
- design specs/tokens allowed;
- visual references allowed;
- sources expressly forbidden (other manuscripts, raw interviews, reference PDFs, archived layouts).

When the user says a document is final, preserve its text/hash and do not “improve” it.

## Component lifecycle

Map the repository's actual states. A useful generic model is:

- `PLANNED`
- `IMPLEMENTED_PENDING_HOST_TEST`
- `RUNTIME_TESTED_PENDING_VISUAL_ACCEPTANCE`
- `APPROVED`
- `FROZEN`
- `SUPERSEDED_BY_EXTERNAL_ARTWORK`
- `PENDING`
- `WIDTH_PENDING`

Do not introduce these exact strings if the repository already has another schema. Approval and freeze are component-specific.

## Frozen or approved scope

Determine:

- which files/scopes are immutable;
- whether the status file lists those paths;
- the baseline tag/commit used for stronger comparison;
- whether a freeze task permits only a status change;
- whether tags and pushes are requested.

Treat user-approved artwork, copy, tokens, and modules as immutable even when the repository does not use the word `FROZEN`.

## Publication geometry

Record the project-specific values rather than assuming a default:

- trim width/height;
- bleed per edge;
- facing-pages policy;
- margins, columns, and gutter;
- binding direction and spine dependency;
- image/link policy;
- output PDF preset or printer requirements.

## Acceptance authority

Clarify which evidence supports each status:

- static source checks;
- native compilation;
- InDesign host runtime;
- generated PDF inspection;
- user visual acceptance;
- printer/preflight acceptance.

Never upgrade a component to `APPROVED` or `FROZEN` using a lower evidence level than the repository requires.

## Delivery contract

Record:

- exact test commands;
- commit message and tag conventions;
- whether push is authorized;
- required final response fields;
- artifacts or diagnostics that must remain untracked/untouched.
