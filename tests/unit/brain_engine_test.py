"""Unit tests for core/scripts/brain.py against a throwaway vault. Run: python tests/unit/brain_engine_test.py"""
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SECRET = "fd51d1dd516b5c9d6f5b51862ac8890a82bb853f3805bf73df68a651352a47a1"


def load_engine(vault, claude_home):
    os.environ["BRAIN_VAULT"] = vault
    os.environ["BRAIN_CLAUDE_HOME"] = claude_home
    spec = importlib.util.spec_from_file_location("brain", os.path.join(ROOT, "core", "scripts", "brain.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def line(**kw):
    return json.dumps(kw) + "\n"


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.vault = os.path.join(self.tmp, "vault")
        self.home = os.path.join(self.tmp, "claude")
        self.repo = os.path.join(self.tmp, "code", "Alpha_Repo")
        os.makedirs(os.path.join(self.vault, "Projects", "alpha-repo"))
        os.makedirs(os.path.join(self.vault, "Projects", "beta"))
        os.makedirs(os.path.join(self.vault, "Claude"))
        os.makedirs(os.path.join(self.home, "projects", "x"))
        os.makedirs(self.repo)
        with open(os.path.join(self.vault, "Claude", "registry.md"), "w") as f:
            f.write("| project | repo | state | cluster | watch | tasks |\n|---|---|---|---|---|---|\n"
                    f"| beta | `{self.tmp}/code/other` | live | trading | - | - |\n")
        with open(os.path.join(self.vault, "Projects", "beta", "beta-status.md"), "w", encoding="utf-8") as f:
            f.write("---\nphase: stale frontmatter\n---\n# beta\n## Current\n**Phase:** P3 — validating\n\n## History\n")
        with open(os.path.join(self.vault, "Projects", "beta", "beta-session-log.md"), "w") as f:
            f.write("## [2026-01-01] | old\n")
        self.b = load_engine(self.vault, self.home)
        self.transcript = os.path.join(self.home, "projects", "x", "sess-1234.jsonl")
        self.write_transcript(1)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_transcript(self, turns):
        with open(self.transcript, "w", encoding="utf-8") as f:
            f.write(line(type="ai-title", aiTitle="Test session"))
            for i in range(turns):
                f.write(line(type="user", cwd=self.repo, entrypoint="cli", timestamp=f"2026-09-26T0{i}:00:00Z",
                             message={"content": f"prompt {i} key {SECRET}"}))
                f.write(line(type="user", toolUseResult={}, timestamp=f"2026-09-26T0{i}:00:01Z",
                             message={"content": [{"type": "tool_result", "content": "OUTPUT MUST NOT APPEAR"}]}))
                f.write(line(type="assistant", timestamp=f"2026-09-26T0{i}:00:02Z", message={"content": [
                    {"type": "tool_use", "name": "Edit", "input": {"file_path": f"{self.repo}/f{i}.py"}},
                    {"type": "tool_use", "name": "Bash", "input": {"command": f'git commit -m "change {i}"'}}]}))

    def run_end(self):
        sys.stdin = io.StringIO(json.dumps({"transcript_path": self.transcript, "reason": "exit"}))
        self.b.cmd_session_end(None)
        return self.b.load_events()

    def test_resolve_basename_normalised_and_registry(self):
        self.assertEqual(self.b.resolve_project(self.repo), "alpha-repo")
        self.assertEqual(self.b.resolve_project(os.path.join(self.tmp, "code", "other", "sub")), "beta")
        self.assertEqual(self.b.resolve_project(os.path.join(self.vault, "Projects", "beta", "x")), "beta")
        self.assertIsNone(self.b.resolve_project(os.path.join(self.tmp, "nowhere")))

    def test_session_end_idempotent_and_continues(self):
        self.assertEqual(len(self.run_end()), 1)
        self.assertEqual(len(self.run_end()), 1, "re-running must not duplicate")
        self.write_transcript(2)
        evs = self.run_end()
        self.assertEqual(len(evs), 2)
        self.assertEqual(evs[1]["part"], 2)
        self.assertEqual(evs[1]["n_prompts"], 1)
        self.assertEqual(evs[1]["commits"], ["change 1"])

    def test_redaction_and_no_tool_output(self):
        self.run_end()
        blob = self.b.read(self.b.EVENTS)
        blob += self.b.read(os.path.join(self.vault, "Claude", "journal", "2026-09-26.md"))
        self.assertNotIn(SECRET, blob)
        self.assertNotIn("OUTPUT MUST NOT APPEAR", blob)
        self.assertIn("[REDACTED]", blob)
        self.assertTrue(os.path.exists(os.path.join(self.vault, "Projects", "alpha-repo", "alpha-repo-activity.md")))

    def test_redact_keeps_paths(self):
        p = "C--Users-someone-code-AI-Trading-View-Stocks-and-more-words"
        self.assertEqual(self.b.redact(p), p)

    def test_phase_prefers_current_over_frontmatter(self):
        text = self.b.read(os.path.join(self.vault, "Projects", "beta", "beta-status.md"))
        self.assertEqual(self.b.parse_phase(text), "P3 — validating")

    def test_auto_block_preserves_manual_text(self):
        p = os.path.join(self.vault, "Claude", "projects-index.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("# Index\nMANUAL TOP\n<!-- AUTO:BEGIN -->\nold\n<!-- AUTO:END -->\nMANUAL BOTTOM\n")
        self.b.replace_auto(p, "new block", "")
        t = self.b.read(p)
        self.assertIn("MANUAL TOP", t)
        self.assertIn("MANUAL BOTTOM", t)
        self.assertIn("new block", t)
        self.assertNotIn("old", t)

    def test_hook_render_keeps_other_projects(self):
        self.b.append_events([
            {"kind": "job", "session_id": "", "date": "2026-09-25", "end": "2026-09-25T10:00+10:00", "project": "beta",
             "source": "t", "message": "beta day1"},
            {"kind": "job", "session_id": "", "date": "2026-09-25", "end": "2026-09-25T11:00+10:00", "project": "alpha-repo",
             "source": "t", "message": "alpha day1"}])
        self.b.render_views(self.b.load_events())
        self.run_end()  # alpha-repo session on 2026-09-26
        day1 = self.b.read(os.path.join(self.vault, "Claude", "journal", "2026-09-25.md"))
        self.assertIn("beta day1", day1)
        self.assertIn("alpha day1", day1)
        self.assertIn("beta day1", self.b.read(os.path.join(self.vault, "Projects", "beta", "beta-activity.md")))

    def test_personal_read_withholds_content(self):
        with open(self.transcript, "a", encoding="utf-8") as f:
            f.write(line(type="assistant", timestamp="2026-09-26T05:00:00Z", message={"content": [
                {"type": "tool_use", "name": "Read", "input": {"file_path": f"{self.vault}/Personal/Daily/x.md"}}]}))
        e = self.run_end()[0]
        self.assertTrue(e["private"])
        self.assertEqual(e["prompts"], [])

    def test_duplicate_part_ignored(self):
        e = self.run_end()[0]
        self.b.append_events([e])
        self.assertEqual(len(self.b.load_events()), 1)

    def test_redact_prose_untouched(self):
        s = "raise the token budget and password policy"
        self.assertEqual(self.b.redact(s), s)
        self.assertIn("[REDACTED]", self.b.redact("token=abcdef123456"))

    def test_uncurated_warning(self):
        self.run_end()
        with open(os.path.join(self.vault, "Projects", "alpha-repo", "alpha-repo-session-log.md"), "w") as f:
            f.write("## [2026-01-01] | x\n")
        warn, _ = self.b.build_health(self.b.load_registry(), self.b.load_events(), {})
        self.assertTrue(any("alpha-repo" in w and "since last curated" in w for w in warn))
        self.assertTrue(any("alpha-repo" in w and "registry" in w for w in warn))


if __name__ == "__main__":
    unittest.main(verbosity=1)
