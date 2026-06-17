# Node: terminal

Sink. The walk is complete. No work, no outgoing edges.

Reached from:
- `handoff` (the normal path — issue filed or failure reported), or
- `classify` / `gather` / `ask-wrap-up` / `ask-create` via `user_cancel` (the user
  bailed before filing — the local `ISSUE.md` draft, if any, is kept).

Do nothing here. The walker stops.
