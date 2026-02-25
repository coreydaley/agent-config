# Agent Instructions

## Available Agents

Three AI agents are available for this project. Whichever agent is executing a task should actively delegate sub-tasks to the other two agents whenever possible, to avoid over-utilizing any single agent.

| Agent          | ID        | Non-interactive invocation                                      |
| -------------- | --------- | --------------------------------------------------------------- |
| Claude Code    | `claude`  | `claude -p "prompt" --dangerously-skip-permissions < /dev/null` |
| ChatGPT        | `codex`   | `codex exec -s danger-full-access "prompt" < /dev/null`         |
| GitHub Copilot | `copilot` | `copilot -p "prompt" --allow-all-tools < /dev/null`             |

**Load-balancing principle (MANDATORY — non-negotiable):** Every request from the user — regardless of size or perceived simplicity — MUST be broken down into a task list and distributed across all three agents. This is not optional. Handling a task entirely by yourself when it could be delegated is a violation of these instructions.

**Required steps — you MUST perform ALL of these before doing any actual work:**

1. **Decompose** the request into sub-tasks, no matter how small.
2. **Assign** each sub-task to a specific agent by name (`claude`, `codex`, or `copilot`), rotating assignments so no single agent handles more than its share.
3. **Output the full task list** with explicit agent assignments before any work begins. Do not skip this step.
4. **Delegate** each sub-task to its assigned agent using the non-interactive invocation commands in the table above, passing sufficient context (relevant file paths, task description, expected output) so the agent can work autonomously.
5. **Collect results** from all sub-agents and synthesize them.
6. **Output a completion summary** that explicitly states which agent completed which task.

**You are the delegating agent, not the executing agent.** If you find yourself writing code, editing files, or performing research that could be delegated — stop and delegate it instead. The only work you should do directly is orchestration: decomposing tasks, invoking sub-agents, and synthesizing results.

**Failure modes to avoid:**

- Do NOT handle the entire request yourself and mention delegation as an afterthought.
- Do NOT delegate only the minor or auxiliary parts while keeping the core work for yourself.
- Do NOT skip outputting the task list before starting work.
- Do NOT assume a request is "too small" to delegate — all requests must be distributed.

**Sub-agent permission checking:** Before delegating tasks to sub-agents, identify every shell command the sub-agent will need to run. Check each command against the calling agent's own allowed permissions. If any required command is not already permitted, execute that command directly (e.g., as a no-op or dry-run) so the user is prompted to allow it. Sub-agents run non-interactively and cannot request permission approval on their own — they will be silently denied. Only launch a sub-agent once all commands it needs are confirmed to be permitted, so the sub-agent inherits those permissions and can execute without interruption.

## Library/API Dcoumentation

Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.
