import json
import zipfile
from pathlib import Path

from helpers import FIXTURES, SklCase, load_skl

skl = load_skl()
NOTES = (FIXTURES / "notes" / "SKILL.md").read_text()


class StoreTests(SklCase):
    def setUp(self):
        super().setUp()
        self.home_skills = Path(self.env["HOME"]) / ".claude" / "skills"

    def test_sync_list_show(self):
        home_skills = self.home_skills
        self.put_skill(home_skills, "notes"); self.put_skill(home_skills, "meal")
        (home_skills / "plain").mkdir(parents=True); (home_skills / "plain" / "SKILL.md").write_text("---\nname: plain\n---\nNo interface.\n")
        r = self.run_cli("sync")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("indexed notes (3 actions)", r.stdout)
        self.assertIn("indexed meal-prep-cookbook-recipe (5 actions)", r.stdout)
        self.assertNotIn("plain", r.stdout + r.stderr)
        self.assertTrue(r.stdout.rstrip().endswith("2 skills indexed"))
        self.assertEqual(self.run_cli("list").stdout.splitlines(),
            ["meal-prep-cookbook-recipe\tadd, update, duplicate, remove, list", "notes\tadd, show, list"])
        shown = self.run_cli("show", "notes").stdout
        self.assertEqual(shown.rstrip("\n"), skl.extract_block(NOTES).rstrip("\n"))
        self.assertEqual(json.loads(self.run_cli("show", "notes", "--parsed").stdout)["usage_line"], "/notes <action> [<target>] [options]")
        self.assertTrue((Path(self.env["XDG_DATA_HOME"]) / "skl" / "skills" / "notes" / "SKILL.md").is_file())

    def test_sync_removes_gone_and_keeps_imports(self):
        p = self.put_skill(self.home_skills, "notes")
        self.run_cli("sync")
        self.run_cli("import", str(FIXTURES / "meal" / "SKILL.md"))
        p.unlink()
        r = self.run_cli("sync")
        self.assertIn("removed notes", r.stdout); self.assertIn("1 skills indexed", r.stdout)
        self.assertEqual(self.run_cli("list").stdout.split("\t")[0], "meal-prep-cookbook-recipe")

    def test_sync_with_no_skills_keeps_imports(self):
        self.run_cli("import", str(FIXTURES / "meal" / "SKILL.md"))
        r = self.run_cli("sync")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.rstrip().endswith("1 skills indexed"))
        self.assertNotIn("removed", r.stdout)
        self.assertIn("meal-prep-cookbook-recipe", self.run_cli("list").stdout)

    def test_project_and_env_roots_and_clash(self):
        work = Path(self.tmp) / "work"; (work / ".git").mkdir()
        (work / "sub").mkdir()
        self.put_skill(self.home_skills, "notes")
        self.put_skill(work / ".claude" / "skills", "notes", folder="notes-project")
        r = self.run_cli("sync", cwd=work / "sub")
        self.assertIn("note: notes from", r.stdout); self.assertIn("1 skills indexed", r.stdout)
        extra = Path(self.tmp) / "extra"; self.put_skill(extra, "meal")
        r = self.run_cli("sync", env={**self.env, "SKL_SKILL_PATH": str(extra)})
        self.assertIn("2 skills indexed", r.stdout)

    def test_import_clash_replaced_by_sync(self):
        self.run_cli("import", str(FIXTURES / "notes" / "SKILL.md"))
        self.put_skill(self.home_skills, "notes")
        r = self.run_cli("sync")
        self.assertIn("note: notes from", r.stdout)
        self.assertTrue(r.stdout.rstrip().endswith("1 skills indexed"))

    def test_passthrough(self):
        d = self.home_skills / "odd"; d.mkdir(parents=True)
        (d / "SKILL.md").write_text("---\nname: odd\n---\n## Command interface\n```\nfree text\n```\n")
        self.assertIn("indexed odd (pass-through)", self.run_cli("sync").stdout)
        self.assertEqual(self.run_cli("list").stdout.strip(), "odd\t(pass-through)")

    def test_bad_inputs(self):
        home_skills = self.home_skills
        d = home_skills / "evil"; d.mkdir(parents=True)
        (d / "SKILL.md").write_text(NOTES.replace("name: notes", "name: ../evil"))
        b = home_skills / "bin"; b.mkdir()
        (b / "SKILL.md").write_bytes(b"\xff\xfe## Command interface\n")
        self.put_skill(home_skills, "notes")
        r = self.run_cli("sync")
        self.assertEqual(r.returncode, 0); self.assertIn("1 skills indexed", r.stdout)
        self.assertEqual(r.stderr.count("skipped "), 2)
        self.assertFalse((Path(self.env["XDG_DATA_HOME"]) / "evil").exists())
        self.assertEqual(sorted(p.name for p in (Path(self.env["XDG_DATA_HOME"]) / "skl" / "skills").iterdir()), ["notes"])

    def test_import_zip_and_errors(self):
        z = Path(self.tmp) / "notes.skill"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("notes/SKILL.md", NOTES); zf.writestr("../escape.txt", "x")
        r = self.run_cli("import", str(z)); self.assertIn("imported notes", r.stdout)
        self.assertFalse((Path(self.tmp) / "escape.txt").exists())
        self.assertFalse((Path(self.env["XDG_DATA_HOME"]) / "escape.txt").exists())
        plain = Path(self.tmp) / "SKILL.md"; plain.write_text("---\nname: plain\n---\nnothing\n")
        r = self.run_cli("import", str(plain)); self.assertEqual(r.returncode, 1); self.assertTrue(r.stderr.startswith("error: "))

    def test_import_folder_and_missing(self):
        r = self.run_cli("import", str(FIXTURES / "notes"))
        self.assertIn("imported notes", r.stdout)
        r = self.run_cli("import", str(Path(self.tmp) / "nope"))
        self.assertEqual(r.returncode, 1); self.assertNotIn("Traceback", r.stderr)
        z = Path(self.tmp) / "empty.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("readme.txt", "x")
        r = self.run_cli("import", str(z))
        self.assertEqual(r.returncode, 1); self.assertIn("error: no SKILL.md in", r.stderr)

    def test_remove_and_unknown_and_corrupt(self):
        self.put_skill(self.home_skills, "notes"); self.run_cli("sync")
        r = self.run_cli("show", "note"); self.assertEqual(r.returncode, 2)
        self.assertIn("error: unknown skill 'note'", r.stderr); self.assertIn("did you mean: notes", r.stderr)
        self.assertIn("removed notes", self.run_cli("remove", "notes").stdout)
        self.assertIn("no skills indexed", self.run_cli("list").stdout)
        (Path(self.env["XDG_DATA_HOME"]) / "skl" / "index.json").write_text("{broken")
        r = self.run_cli("list"); self.assertEqual(r.returncode, 1); self.assertIn("run 'skl sync'", r.stderr); self.assertNotIn("Traceback", r.stderr)

    def test_corrupt_and_oversized_zip(self):
        z = Path(self.tmp) / "bad.skill"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("notes/SKILL.md", NOTES)
        raw = bytearray(z.read_bytes())
        raw[raw.index(b"Fixture skill")] ^= 0xFF
        z.write_bytes(bytes(raw))
        r = self.run_cli("import", str(z))
        self.assertEqual(r.returncode, 1); self.assertTrue(r.stderr.startswith("error: "), r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        big = Path(self.tmp) / "big.zip"
        with zipfile.ZipFile(big, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("notes/SKILL.md", NOTES + "x" * (2 * 1024 * 1024))
        r = self.run_cli("import", str(big))
        self.assertEqual(r.returncode, 1); self.assertTrue(r.stderr.startswith("error: "), r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_name_regex(self):
        for bad in ("a\n", "a b", "../x", "a/b", "a:b"):
            self.assertIsNone(skl._NAME_RE.fullmatch(bad), bad)
        for good in ("notes", "a.b-c_d", "A1"):
            self.assertIsNotNone(skl._NAME_RE.fullmatch(good), good)
