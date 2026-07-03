# Node: terminal

Sink. Print a brief confirmation and stop.

## Steps

1. **Print a one-line summary** based on the last transition:
   - From `image → terminal`: confirm the post and its artifacts, e.g.
     - Final post: `content/posts/$YYYY/$MM/$SLUG/index.md`
     - Intermediate drafts: `$DRAFTS_DIR` (`~/Reports/<org>/<repo>/blog-posts/$SLUG/`)
   - From `init → terminal [help]`: nothing extra — the help text was already printed.

2. **Stop.** No transitions, no further work.

## Outputs

- Brief printed confirmation.

## Outgoing edges

None. Terminal is a sink.

## Don'ts

- **Don't commit or push.** Writing the post is the deliverable; committing is always a separate, explicit user action.
- **Don't publish or post anywhere.** There is no social/LinkedIn step.
- **Don't suggest next commands.** The user knows what's next.
