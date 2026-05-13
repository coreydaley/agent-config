#!/usr/bin/env python3
"""Validate mermaid code blocks in markdown files using mmdc.

Extracts ```mermaid ... ``` fences from each given file, renders each
through `mmdc` to a throwaway SVG, and reports parse errors with the
correct file:line so editors can jump to them.

Usage:
    lint-mermaid.py <file.md> [<file.md> ...]

Exit codes:
    0  all blocks parse cleanly (or no blocks found)
    1  at least one block failed
    2  mmdc not on PATH
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FENCE_RE = re.compile(r"^```mermaid\s*$")
END_RE = re.compile(r"^```\s*$")


def extract_blocks(path: Path):
    """Yield (start_line_1based, block_text) for each mermaid fence."""
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        if FENCE_RE.match(lines[i]):
            start = i + 2  # first line inside the fence (1-based)
            body = []
            i += 1
            while i < len(lines) and not END_RE.match(lines[i]):
                body.append(lines[i])
                i += 1
            yield start, "\n".join(body)
        i += 1


def validate_block(text: str) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "diagram.mmd"
        out = Path(td) / "diagram.svg"
        src.write_text(text)
        proc = subprocess.run(
            ["mmdc", "--quiet", "-i", str(src), "-o", str(out)],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            return True, ""
        return False, trim_mmdc_error(proc.stdout + proc.stderr)


def trim_mmdc_error(msg: str) -> str:
    """Drop puppeteer/node stack traces; keep just the parse error."""
    kept = []
    for line in msg.splitlines():
        stripped = line.strip()
        # First stack-frame marker — everything below is noise.
        if stripped.startswith("at ") or stripped.startswith("Parser.parseError"):
            break
        kept.append(line)
    return "\n".join(kept).strip()


def shift_line_refs(msg: str, offset: int) -> str:
    """Rewrite 'Parse error on line N' to point at the actual file line."""

    def repl(m):
        return f"Parse error on line {int(m.group(1)) + offset}"

    return re.sub(r"Parse error on line (\d+)", repl, msg)


def main(argv: list[str]) -> int:
    if not shutil.which("mmdc"):
        print("lint-mermaid: mmdc not found on PATH", file=sys.stderr)
        return 2

    errors = 0
    for arg in argv:
        path = Path(arg)
        if not path.is_file():
            continue
        for start, block in extract_blocks(path):
            ok, msg = validate_block(block)
            if ok:
                continue
            errors += 1
            shifted = shift_line_refs(msg, start - 1)
            print(f"{path}:{start}: mermaid parse error", file=sys.stderr)
            print(shifted, file=sys.stderr)
            print("", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
