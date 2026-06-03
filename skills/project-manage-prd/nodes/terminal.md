# Node: terminal

Sink. The run is over.

## Reached from

- `handoff` (normal completion — PRD published or publish reported failed)
- `discuss` (`user_cancel`) — user bailed mid-discussion
- `ask-wrap-up` (`user_cancel`) — user bailed before drafting
- `ask-publish` (`user_cancel`) — user bailed before publishing

## Behavior

No work. The preceding node already printed whatever the user needs (the wiki
URL on success, the local draft path on cancel/failure).

## Notes

- **Don't reprint.** `handoff` (or the cancel) already said what matters.
- **Nothing to clean up.** The working draft at `$SESSION_DIR/PRD.md` is durable
  on purpose — on cancel or publish-failure it's the user's fallback.
- **Forgejo is untouched on any cancel route.** The wiki is written only by
  `publish`, which is reachable only through the `ask-publish` → `user_publish`
  approval.
