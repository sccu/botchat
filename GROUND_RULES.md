# Ground Rules

This document defines the foundational rules that **all contributors — human or agent — must follow** when working on `agent-gadget`.

---

## 1. Dependency Direction

The project enforces a strict dependency flow:

```
rule → document → code
```

- **Rules** (this file) are the upstream source of truth.
- **Documents** (`AGENTS.md`, `docs/`, including Knowledge Base `docs/kb/`) are derived from these rules.
- **Code** (`src/`, `tests/`) is derived from the documents.

When a defect is found, the fix should target the **highest upstream layer** responsible, not just patch the code.

- **Project Layout**: The exact directory structure of the project is maintained in `docs/architecture.md`. Any structural changes (adding/removing directories or key files) **MUST** be synchronized with `docs/architecture.md`.

## 2. Fail-Fast Over Silent Recovery

Do not mask errors with fallback branches. If an operation encounters an unexpected state, raise an error immediately.

## 3. Simplicity

- No speculative abstractions. Write code for current requirements only.
- If a function exceeds 50 lines, consider splitting it.
- Prefer modifying existing code over adding new files when the change is small.

## 4. Testing

- Test frameworks: **pytest** (unit) and **Playwright** (browser / E2E).
- Add new test cases to existing test files before creating new ones.
- Do **not** use mock data unless explicitly approved.
- Run the full test suite before pushing: `pytest`.

## 5. Pre-Commit

A `pre-commit` hook runs `pytest` on every commit. All tests must pass before code is committed.

## 6. Clean Architecture

- Policy functions call mechanism functions, not the other way around.
- Keep side effects (I/O, network) at the boundary; keep core logic pure.

## 7. Surgical Changes

- Every changed line must trace directly to the task at hand.
- Do not refactor adjacent code that is not broken.
- Match the existing code style.

## 8. Agent Boundaries

Every agent skill must strictly operate within its defined scope in `SKILL.md` and `AGENTS.md`. Over-action beyond the stated role (e.g., modifying code during an audit or research) is strictly prohibited, even if it appears helpful. If a task requires actions outside the current skill's scope, the agent must report this to the user instead of executing it.

## 9. Language Policy


To ensure clarity and consistency in human-agent interaction:
- **English**: All skill definitions (`SKILL.md`), workflow definitions (`workflows/*.md`), system prompts, and implementation plans must be written in English.
- **Korean**: All primary human-interaction artifacts, including GitHub Issues, `research_report.md`, `design_report.md`, and `review_report.md`, must be written in Korean.
