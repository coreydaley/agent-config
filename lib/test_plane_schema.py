"""Unit tests for plane_schema. Run: python3 -m unittest lib/test_plane_schema.py"""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from plane_schema import (
    Cycle,
    Epic,
    Milestone,
    Module,
    Project,
    STATES,
    SEVERITY_TO_PRIORITY,
    TRANSITIONS,
    Workspace,
    WorkItem,
    join_frontmatter,
    slugify,
    split_frontmatter,
    validate_transition,
)


class FrontmatterTests(unittest.TestCase):
    def test_split_no_frontmatter(self):
        meta, body = split_frontmatter("plain body\n")
        self.assertEqual(meta, {})
        self.assertEqual(body, "plain body\n")

    def test_split_with_frontmatter(self):
        text = "---\nid: SEC-001\ntitle: foo\n---\n\nbody here\n"
        meta, body = split_frontmatter(text)
        self.assertEqual(meta, {"id": "SEC-001", "title": "foo"})
        self.assertEqual(body, "\nbody here\n")

    def test_join_drops_empty(self):
        out = join_frontmatter({"id": "X", "labels": [], "skip": None, "keep": "y"}, "body\n")
        self.assertIn("id: X", out)
        self.assertIn("keep: y", out)
        self.assertNotIn("labels:", out)
        self.assertNotIn("skip:", out)


class SlugifyTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Streaming I/O"), "streaming-i-o")
        self.assertEqual(slugify("  Hello, World!  "), "hello-world")
        self.assertEqual(slugify(""), "untitled")


class WorkItemRoundtripTests(unittest.TestCase):
    def test_minimal_roundtrip(self):
        wi = WorkItem(
            id="SEC-001", title="Reintroduce entitlements file",
            project="purrchiver", workspace="coreydaley-com",
            audit_id="SEC-001", audit_type="apple-security",
            audit_severity="critical", source="audit",
            priority="urgent",
        )
        wi.description = "Sandbox surface is unreviewable."
        wi.acceptance = "Entitlements file present and reviewed."
        wi.append_activity("Created from audit ingest")

        text = wi.to_text()
        self.assertIn("id: SEC-001", text)
        self.assertIn("priority: urgent", text)
        self.assertIn("audit_type: apple-security", text)
        self.assertIn("## Description", text)
        self.assertIn("## Activity log", text)

        wi2 = WorkItem.from_text(text)
        self.assertEqual(wi2.id, wi.id)
        self.assertEqual(wi2.priority, "urgent")
        self.assertEqual(wi2.audit_type, "apple-security")
        self.assertEqual(wi2.description, wi.description)
        self.assertEqual(wi2.acceptance, wi.acceptance)
        self.assertEqual(len(wi2.activity_log), 1)
        self.assertIn("Created from audit ingest", wi2.activity_log[0])

    def test_validation(self):
        wi = WorkItem(id="X-1", title="ok", project="p", workspace="w")
        self.assertEqual(wi.validate(), [])
        wi.state = "bogus"
        self.assertTrue(wi.validate())

    def test_severity_priority_map(self):
        for sev, pri in SEVERITY_TO_PRIORITY.items():
            self.assertIn(pri, {"urgent", "high", "medium", "low", "none"})

    def test_state_transitions_have_no_cycles_into_cancelled(self):
        self.assertEqual(TRANSITIONS["cancelled"], set())
        # completed can only re-open to started — no skipping back to backlog
        self.assertEqual(TRANSITIONS["completed"], {"started"})


class FileIoTests(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "SEC-001.md"
            wi = WorkItem(
                id="SEC-001", title="t", project="purr", workspace="coreydaley-com",
                audit_type="apple-security", audit_id="SEC-001",
            )
            wi.save(p)
            self.assertTrue(p.exists())
            wi2 = WorkItem.load(p)
            self.assertEqual(wi2.id, "SEC-001")

    def test_workspace_save_load(self):
        with tempfile.TemporaryDirectory() as td:
            # Override $HOME so reports_base() points into tempdir.
            import os
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = td
            try:
                ws = Workspace(id="coreydaley-com", name="Corey Daley",
                               description="Portfolio workspace.")
                ws.save()
                loaded = Workspace.load("coreydaley-com")
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded.name, "Corey Daley")
                self.assertEqual(loaded.description, "Portfolio workspace.")
            finally:
                if old_home is not None:
                    os.environ["HOME"] = old_home

    def test_project_save_load(self):
        with tempfile.TemporaryDirectory() as td:
            import os
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = td
            try:
                pr = Project(id="purrchiver", name="Purrchiver",
                             workspace="coreydaley-com",
                             ship_target="v0.1 MAS submission")
                pr.save()
                loaded = Project.load("coreydaley-com", "purrchiver")
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded.name, "Purrchiver")
                self.assertEqual(loaded.ship_target, "v0.1 MAS submission")
            finally:
                if old_home is not None:
                    os.environ["HOME"] = old_home


class CycleTests(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as td:
            import os
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = td
            try:
                c = Cycle(
                    id="2026-05-22--cycle-001",
                    name="Purrchiver v0.1 — Cycle 1",
                    project="purrchiver", workspace="coreydaley-com",
                    goal="Close out audit P0/P1 + ship gates",
                    start_date="2026-05-22", end_date="2026-05-29",
                    exit_criteria=["Zero High audit findings",
                                   "Re-audit returns only nits"],
                )
                c.save()
                loaded = Cycle.load("coreydaley-com", "purrchiver",
                                    "2026-05-22--cycle-001")
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded.name, "Purrchiver v0.1 — Cycle 1")
                self.assertEqual(len(loaded.exit_criteria), 2)
                cycles = Cycle.list("coreydaley-com", "purrchiver")
                self.assertEqual(len(cycles), 1)
            finally:
                if old_home is not None:
                    os.environ["HOME"] = old_home


class NamedEntityTests(unittest.TestCase):
    def test_module_epic_milestone(self):
        with tempfile.TemporaryDirectory() as td:
            import os
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = td
            try:
                Module(id="security", name="Security",
                       project="purrchiver", workspace="coreydaley-com").save()
                Epic(id="streaming-io", name="Streaming I/O refactor",
                     project="purrchiver", workspace="coreydaley-com").save()
                Milestone(id="v0.1", name="v0.1 MAS submission",
                          project="purrchiver", workspace="coreydaley-com").save()
                self.assertIsNotNone(
                    Module.load("coreydaley-com", "purrchiver", "security"))
                self.assertIsNotNone(
                    Epic.load("coreydaley-com", "purrchiver", "streaming-io"))
                self.assertIsNotNone(
                    Milestone.load("coreydaley-com", "purrchiver", "v0.1"))
            finally:
                if old_home is not None:
                    os.environ["HOME"] = old_home


class TransitionTests(unittest.TestCase):
    def test_allowed(self):
        self.assertIsNone(validate_transition("backlog", "started"))
        self.assertIsNone(validate_transition("started", "completed"))
        # No-op transition is fine
        self.assertIsNone(validate_transition("completed", "completed"))
        # Re-open from completed
        self.assertIsNone(validate_transition("completed", "started"))

    def test_disallowed(self):
        # Cancelled is terminal
        self.assertIsNotNone(validate_transition("cancelled", "started"))
        # Can't skip completed → backlog (need started → unstarted → backlog path)
        self.assertIsNotNone(validate_transition("completed", "backlog"))


if __name__ == "__main__":
    unittest.main()
