# Node: terminal

Sink. The run is over.

## Reached from

- `handoff` (normal completion — issue filed, or filing reported failed)
- `discuss` (`user_cancel`) — user bailed mid-discussion
- `ask-wrap-up` (`user_cancel`) — user bailed before drafting
- `ask-create` (`user_cancel`) — user bailed before filing

## Behavior

No work. The preceding node already printed whatever the user needs (the issue
URL + next-step chain on success, the local draft path on cancel/failure).

## Notes

- **Don't reprint.** `handoff` (or the cancel) already said what matters.
- **Nothing to clean up.** The working draft at `$SESSION_DIR/FEATURE.md` is kept
  on purpose — on cancel or a failed create it's the user's fallback.
- **Forgejo is untouched on any cancel route.** The issue is filed only by
  `create-issue`, reachable only through the `ask-create` → `user_create`
  approval.
