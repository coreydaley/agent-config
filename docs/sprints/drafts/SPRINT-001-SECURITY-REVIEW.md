# Sprint 001 Security Review

## Summary

This sprint is fundamentally a file system configuration manager: it reads Markdown source files, generates text artifacts, and creates symlinks in the user's home directory. The attack surface is narrow but the impact radius is significant — any content placed in these files flows directly into AI agent system prompts, influencing every interaction those agents have.

---

## Findings

### CRITICAL

**None.**

---

### HIGH

#### H1: Symlink-based agent prompt injection via repo write access

**Section:** Security Considerations, Architecture

**Finding:** The entire threat model rests on the assumption that only the repo owner writes to this repository. Any path where an attacker gains write access to `agents/_GLOBAL.md`, `agents/<agent>/_<AGENT>.md`, `commands/*.md`, or `skills/*/SKILL.md` means they can inject arbitrary instructions into the system prompt of every AI agent the user runs. This is a supply-chain-style attack surface.

**Rating:** High

**Mitigation (incorporated into DoD):**
- Add a warning in `SECURITY.md` and `README.md` that this repo controls agent behavior and should not be world-writable, shared with untrusted collaborators, or cloned from untrusted forks without review
- The existing `SECURITY.md` (created earlier in this session) already covers this; ensure the README also links to it

**DoD addition:** README includes a callout warning that repo contents flow directly into agent system prompts.

---

#### H2: `configure-codex-skills.sh` (P1) modifies user config without rollback

**Section:** P1-A

**Finding:** The planned `configure-codex-skills.sh` script appends entries to `~/.codex/config.toml`. If it runs twice (non-idempotent), it could write duplicate entries. If `config.toml` is malformed before the script runs, the script could produce an unparseable TOML file, breaking Codex entirely for the user. There is no backup step planned for this file.

**Rating:** High

**Mitigation (incorporated into P1-A notes):**
- The script must back up `~/.codex/config.toml` before modifying it (same `.old` pattern as symlink scripts)
- The script must validate the file is well-formed TOML before and after modification (or at minimum, use append-only operations that cannot break existing content)
- Idempotency check: scan for existing path entries before appending
- This is already out of `make all`; the explicit-only invocation reduces exposure

---

### MEDIUM

#### M1: awk-based TOML conversion has no output sanitization

**Section:** P0-C, Conversion spec

**Finding:** The `generate-gemini-commands.sh` script will use `awk` to extract content from Markdown files and embed it verbatim in TOML output. If a command's body contains characters that break TOML triple-quoted strings (e.g., `"""` sequences, or certain control characters), the output TOML file will be malformed. Gemini CLI would either reject it silently or parse incorrectly.

**Rating:** Medium

**Mitigation (incorporated into P0-C conversion constraints):**
- Already added to sprint: document that embedded triple-quoted strings are a known limitation
- Add a post-conversion check: `grep -c '"""' build/gemini-commands/*.toml` and warn if the count is odd (unbalanced)
- Consider using `\'\'\'` or escaping as a defensive measure if Gemini TOML supports it

#### M2: Backup collision in utils.sh

**Section:** Architecture, scripts/utils.sh

**Finding:** The `create_symlink` function backs up existing files by appending `.old`. If a `.old` file already exists at the same path, it is silently overwritten without another backup, permanently destroying the previous backup. This is a data-loss vector for users who run `make all` multiple times with real files at the symlink destinations.

**Rating:** Medium

**Mitigation:** Add a timestamp or counter suffix to backup filenames when `.old` already exists (e.g., `.old.1`, `.old.2`) — or at minimum, check if `.old` exists before overwriting. Not blocking Sprint 001 but should be noted in known limitations.

#### M3: Agent home directory creation via ensure_dir

**Section:** P0-F, utils.sh

**Finding:** The planned `ensure_dir` function will create `~/.codex/`, `~/.gemini/`, etc. if they don't exist. For agents the user has never installed, this creates config directories that look like the agent is configured, which could be confusing and might interfere with future agent installation.

**Rating:** Medium (Low for typical users, Medium for multi-user or managed environments)

**Mitigation:** `ensure_dir` should print a notice when it creates a directory that didn't previously exist. Low friction fix.

---

### LOW

#### L1: No integrity verification for skill files loaded into agent context

**Section:** Architecture, skills/

**Finding:** `skills/` is symlinked as a whole directory. Any file added to `skills/` (e.g., by a dependency, a compromised package, or a confused user) will be automatically available to agents without review. There is no allowlist or integrity check.

**Rating:** Low (inherent to the design; the fix would require a different architecture)

**Mitigation:** Document in README that all files in `skills/` will be available to agents; review additions carefully.

#### L2: Generated TOML files in build/ are not signed or checksummed

**Section:** P0-C, build/

**Finding:** `build/gemini-commands/` is gitignored. There is no mechanism to detect if generated files were tampered with between `make generate` and `make symlinks`.

**Rating:** Low (local-only attack surface; requires prior local access)

**Mitigation:** Out of scope for Sprint 001; acceptable risk for a developer-tool repo.

---

## DoD Additions (Incorporated)

The following items were added to the sprint document as a result of this review:

1. **H1**: README must include a callout warning that repo contents flow directly into agent system prompts and should be reviewed before use.
2. **H2**: P1-A `configure-codex-skills.sh` must back up `~/.codex/config.toml` before modifying it.
3. **M1**: Post-conversion check: warn if converted `.toml` files contain potentially unbalanced `"""` sequences.

Items M2, M3, L1, L2 are noted as known limitations, not sprint blockers.

---

## Threat Model Summary

**Realistic adversarial scenario:** A developer clones this repo (or a fork of it), runs `make all`, and unknowingly loads malicious agent instructions planted in `_GLOBAL.md` or a skill file. The injected instructions silently modify agent behavior — for example, exfiltrating code snippets to an attacker-controlled endpoint via shell commands the agent is prompted to run.

**Mitigations in place:** The repo is a personal dotfiles-style tool intended for single-owner use. The `SECURITY.md` and README warnings reduce the risk of trusting unreviewed forks. The actual attack requires an attacker to already control the repo content.

**Residual risk:** Acceptable for a developer productivity tool with clear documentation. Not appropriate for shared infrastructure or multi-user environments without additional controls.
