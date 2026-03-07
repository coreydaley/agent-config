# Sprint 001 Merge Notes

## Claude Draft Strengths
- Comprehensive capability matrix with exact filesystem paths per agent
- Clear data-flow diagram showing what flows where
- Phase-based implementation plan with specific file-level tasks
- Detailed Definition of Done with observable filesystem assertions
- Gemini command conversion pipeline design was well-conceived
- Risk table with specific mitigations

## Codex Draft Strengths
- "Capability-routed model" framing is a better mental model than the per-agent loop
- Guiding principles section (idempotency, explicit skips, Bash 3.2 compat)
- Stretch goals section prevents scope bleed
- Execution order section makes dependencies explicit
- "Decisions Needed Before Implementation" surfacing blockers upfront
- Stricter scope management overall

## Valid Critiques Accepted

### Sprint scope tightening (HIGH)
Codex correctly identified that my draft over-scoped. The P0/P1/Deferred structure from Codex's critique is adopted. Sprint Infrastructure (ledger.tsv, docs/sprints/README.md) is moved to Deferred since we're bootstrapping those as part of the superplan process itself, not as a sprint deliverable.

### Gemini subagent contradiction (HIGH)
My draft listed Gemini subagents as supported but then said "format TBD" and excluded them from implementation. Resolution: Gemini subagents are IN-SCOPE for Sprint 001 at the symlink level only. The `~/.gemini/agents/` symlink will be created. Format/frontmatter requirements are documented but conversion is deferred.

### Idempotency in DoD (MEDIUM)
Added explicit idempotency criterion: `make all` run twice must produce same result.

### Explicit skip logs (MEDIUM)
Added requirement that unsupported features emit explicit `echo` skip messages rather than silent no-ops.

### Source file error handling (MEDIUM)
Added requirement that `generate-agent-files.sh` fails explicitly if `_GLOBAL.md` or `_<AGENT>.md` is missing.

## Critiques Rejected

### "Move sprint ledger to deferred" (REJECTED)
The ledger skill and sprint infrastructure already exist in the repo and we're using them in this very sprint. Keeping the ledger initialization in the sprint as a stretch goal so the tooling is validated end-to-end.

### "Defer Gemini command conversion to P1" (REJECTED)
The user explicitly answered this question in the interview: auto-convert at build time is the chosen approach. Gemini conversion stays in P0.

### "Defer Codex config.toml skill registration" (MODIFIED)
Codex recommended deferring; user answered they want config.toml generation. Keeping as P1 (not P0) since it modifies a user config file and carries more risk.

## Interview Refinements Applied

1. **Gemini commands**: Auto-convert at build time confirmed → `scripts/generate-gemini-commands.sh` + `build/gemini-commands/` in P0
2. **Subagents**: Single dir, superset frontmatter confirmed → `subagents/*.md` with `name:`, `description:`, `tools:` fields works for Claude, Gemini; Copilot needs a `.agent.md` conversion step (added as P1)
3. **Content scope**: Write starter content confirmed → reduced to minimal non-empty stubs to validate the pipeline, not rich instructions
4. **Codex skills**: Generate config.toml entries confirmed → moved to P1 (user wants it, but it modifies user config so needs care)

## Final Decisions

| Decision | Choice |
|---|---|
| Gemini commands | Auto-convert md→toml at build time; output to `build/gemini-commands/` |
| Subagents source | `subagents/` dir (not `agents/`) |
| Subagent format | Single superset frontmatter; Copilot .agent.md conversion in P1 |
| Gemini subagents | Symlink in P0, format docs only; conversion deferred |
| Generated artifact location | In-place for agent files; `build/` only for Gemini TOML conversion |
| Codex skills | P1: optional `scripts/configure-codex-skills.sh` writes config.toml entries |
| Agent content | Minimal stubs (non-empty, smoke-test-ready) in P0 |
| Sprint infrastructure | Stretch goal; not blocking |
