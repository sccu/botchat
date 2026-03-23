# Agents

This document describes the agent skills and workflows available in `agent-gadget`.

---

## Skills

Skills are invoked with `@<skill-name>`. Each skill lives under `.agents/skills/<name>/SKILL.md`.

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `gh-issue` | `@gh-issue <prompt>` | Generates a GitHub Issue via `gh` CLI |
| `research` | `@research` | Deep codebase analysis; outputs `research_report.md` artifact |
| `design` | `@design` | Detailed architecture design; outputs `design_report.md` artifact |
| `review` | `@review` | Code review & QA; outputs `review_report.md` artifact |
| `audit` | `@audit` | Compares docs vs. code; outputs `audit_report.md` artifact |
| `nobot` | `@nobot` | Human-like browser automation via Real Chrome CDP |
| `pr-create` | `@pr-create <issue-id>` | Creates a PR, auto-merges it, and cleans up workspace |

### Skill Authoring Rules

1. Every skill must have a `SKILL.md` with YAML frontmatter (`name`, `description`, `version`, `author`, `category`, `tags`).
2. A skill must **not** perform actions outside its stated role (e.g., `review` must not modify code).
3. Skills that produce reports must write them as **artifacts**, not as chat messages.
4. **Language Policy**: Skill/Agent definitions must be in **English**. However, primary artifacts (e.g., issues, research/design/review reports) must be in **Korean**.

## Knowledge Base

Agents should consult the **Knowledge Base** (`docs/kb/`) when performing tasks that require technical context or troubleshooting.
- **Location:** `docs/kb/`
- **Purpose:** Stores technical documentation, best practices, and troubleshooting tips (e.g. Git workflows, language patterns).
- **Responsibility:** If an agent discovers a new pattern or resolves a complex issue, they should document it as a new markdown file in `docs/kb/`.
- **Formatting:** Every knowledge base document MUST start with a YAML frontmatter block containing `title`, `description`, and `tags`.
  ```yaml
  ---
  title: [Short descriptive title]
  description: [Brief summary of the content]
  tags: [tag1, tag2]
  ---
  ```

## Workflows

Workflows are invoked with `/<workflow-name>`. Each workflow lives under `.agents/workflows/<name>.md`.

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `handle-issue` | `/handle-issue #<id>` | End-to-end issue resolution using a dedicated worktree for environment isolation. |

### Workflow: `handle-issue`

**Role**: Automates the full development lifecycle for a GitHub issue — from branch creation to merge — with minimal human intervention.
- The workflow starts by validating that the target issue has the `status: confirmed` label and does not have the `status: in-progress` label.

**Agent interactions**:
- Invokes `@research` to deeply analyze the issue and codebase context before any implementation begins. The output (`research_report.md`) is the basis for the implementation plan.
- Invokes `@review` after implementation to assess code quality. The output (`review_report.md`) drives iterative refinement until quality standards are met.

### General Agent Behavior

- Agents should typically operate on the current branch for direct interactions and prompt-based tasks.
- Dedicated worktree isolation (`.worktrees/`) is strictly reserved for the `/handle-issue` workflow to ensure that automated processes do not interfere with the main workspace.
