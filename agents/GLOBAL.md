## Available Agents

Three AI agents are available for this project. Whichever agent is executing a task should actively delegate sub-tasks to the other two agents whenever possible, to avoid over-utilizing any single agent.

| Agent          | ID        | Non-interactive invocation              |
| -------------- | --------- | --------------------------------------- |
| Claude Code    | `claude`  | `claude -p "prompt"`                    |
| ChatGPT        | `codex`   | `codex exec "prompt"`                   |
| GitHub Copilot | `copilot` | `copilot -p "prompt" --allow-all-tools` |

**Load-balancing principle:** No agent should handle an entire large task alone. Before starting any multi-step task, decompose it into sub-tasks and distribute them across all three agents as evenly as possible — regardless of task type. No agent is preferred over another; rotate assignments to keep utilization balanced. Pass sufficient context (relevant file paths, task description, expected output) when delegating so the receiving agent can work autonomously. Prefer delegation over doing everything yourself.
