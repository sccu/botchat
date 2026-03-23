---
description: Automatically handles a GitHub issue from branch creation to implementation, AI review, and PR creation using the pr-create skill.
---

> [!IMPORTANT]
> **MANDATORY ISOLATION & ARTIFACT RULES**:
> 1. **Worktree Isolation**: All git and file system operations MUST be executed within a dedicated `.worktrees/<branch-name>` directory. Never modify the main workspace.
> 2. **Relative Paths**: Always use relative paths referenced from the current worktree directory.
> 3. **Artifact Storage**: All generated reports (e.g., `research_report.md`, `design_report.md`, `review_report.md`) MUST be saved strictly in the `tmp/` directory provided in metadata. Never save them in the project root or source directories.

**Workflow Steps:**

0. **Workflow Meta-Planning (MANDATORY)**: Before taking any action, list steps 1-12 as a checklist. Identify the skills to be invoked, artifacts to be generated, and success criteria for each step.
1. **Initialization**: Ask the user for the GitHub Issue ID or Issue Number and wait for input.
2. **Validation**: Invoke the `@gh-issue` skill to verify the issue and update its status. If verification fails, halt the workflow and inform the user.
3. **Branch Setup**: Determine an appropriate branch name (e.g., `issue-<id>-brief-description`).
4. **Isolation Checkpoint (CRITICAL)**: Run the following command:
   `git fetch origin main && git worktree add .worktrees/<branch-name> -b <branch-name> origin/main && cd .worktrees/<branch-name>`
   Verify you are inside the `.worktrees/` directory before proceeding.
5. **Research (Optional)**: Invoke the `@research` skill with the issue number if context is required.
6. **Design (MANDATORY)**: Invoke the `@design` skill with the issue number.
7. **Planning**: Write a detailed implementation plan based on `tmp/research_report.md` (if available) and `tmp/design_report.md`.
8. **Implementation**: Implement the code changes exactly according to the plan within the isolated worktree.
9. **Review**: Invoke the `@review` skill with the issue number to analyze the changes.
10. **Iterative Refinement (LOOP)**: Read `tmp/review_report.md`. If issues exist, refactor and repeat step 9 until the artifact states there are no further issues or review items.
11. **PR Creation**: Invoke the `@pr-create` skill with the issue ID to push the branch, create a PR, and clean up.
12. **Final Output**: Present the final results including the Issue URL and Pull Request URL outputted by `@pr-create`.