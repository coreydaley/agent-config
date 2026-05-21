---
description: >-
  Dual-agent Apple platform persistence audit — SwiftData / Core Data / GRDB
  schema design, migration safety, fetch efficiency, predicate quality, batch
  operations, threading (background contexts, @MainActor boundaries), CloudKit
  sync via NSPersistentCloudKitContainer, conflict resolution. High value for
  SwiftData + CloudKit apps.
disable-model-invocation: true
---

Invoke the `audit-apple-persistence` subagent via the Agent tool. Pass the scope from `$ARGUMENTS` as the prompt (or pass "current working directory" if `$ARGUMENTS` is empty). Pass `--diff-only` through if present.
