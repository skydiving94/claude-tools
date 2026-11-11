import pathlib

from helpers import SklCase, load_skl, FIXTURES

skl = load_skl()


class CompleteTests(SklCase):
    def setUp(self):
        super().setUp()
        src = self.tmp / "home" / ".claude" / "skills"
        self.put_skill(src, "notes")
        self.put_skill(src, "meal")
        r = self.run_cli("sync")
        self.assertEqual(r.returncode, 0, r.stderr)
        import os
        old = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = self.env["XDG_DATA_HOME"]
        self.addCleanup(
            lambda: os.environ.__setitem__("XDG_DATA_HOME", old)
            if old is not None else os.environ.pop("XDG_DATA_HOME", None))
        self.index = skl.load_index()

    def c(self, *words):
        return [x for x, _ in skl.complete(self.index, list(words))]

    def cli(self, *words):
        return self.run_cli("__complete", "--", *words)

    def test_first_word(self):
        c = self.c
        self.assertEqual(c(""), ["sync", "import", "list", "show", "remove", "doctor", "completion", "run", "meal-prep-cookbook-recipe", "notes"])
        self.assertEqual(c("me"), ["meal-prep-cookbook-recipe"])
        self.assertEqual(c("s"), ["sync", "show"])

    def test_builtin_args(self):
        c = self.c
        self.assertEqual(c("show", ""), ["meal-prep-cookbook-recipe", "notes"])
        self.assertEqual(c("completion", ""), ["zsh", "bash"])
        self.assertEqual(c("import", ""), [])
        self.assertEqual(c("run", "notes", "l"), ["list"])

    def test_actions_with_descriptions(self):
        self.assertEqual(skl.complete(self.index, ["notes", ""]),
                         [("add", "Create a note"), ("show", "Show one note or the latest"), ("list", "List notes")])
        self.assertEqual(self.c("meal-prep-cookbook-recipe", "up"), ["update"])

    def test_flags(self):
        c = self.c
        self.assertEqual(c("notes", "add", "t", "--"), ["--commit", "--help", "--tag", "--no-index", "--print", "--app"])
        self.assertEqual(c("notes", "add", "t", "--commit", "--"), ["--help", "--tag", "--no-index", "--print", "--app"])
        self.assertEqual(c("meal-prep-cookbook-recipe", "update", "ossobuco", "--sw"), ["--swap"])
        self.assertEqual(c("notes", "list", "--format", ""), ["short", "long"])
        self.assertEqual(c("notes", "add", "t", "--tag", ""), [])
        self.assertEqual(c("notes", "bogus", "--"), [])

    def test_passthrough_and_skl_prefix(self):
        idx = {"version": 1, "skills": {
            "plain": {"name": "plain", "interface": None},
            "clash": {"name": "clash", "interface": {
                "usage_line": "u", "actions": {"go": {"targets": [], "description": ""}},
                "groups": [{"label": "G", "actions": None, "flags": [
                    {"names": ["--print"], "takes_value": False, "choices": []}]}]}}}}
        self.assertEqual([x for x, _ in skl.complete(idx, ["plain", ""])], ["--help", "--print", "--app"])
        self.assertEqual([x for x, _ in skl.complete(idx, ["clash", "go", "--"])],
                         ["--print", "--skl-print", "--app"])

    def test_cli_output_and_robustness(self):
        r = self.cli("notes", "a")
        self.assertEqual(r.stdout, "add\tCreate a note\n")
        self.assertEqual(self.cli("s").stdout, "sync\nshow\n")
        r = self.cli("nosuchskill", "")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        (pathlib.Path(self.env["XDG_DATA_HOME"]) / "skl" / "index.json").write_text("{broken")
        r = self.cli("no")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertEqual(self.cli("sy").stdout, "sync\n")

    def test_missing_index(self):
        (pathlib.Path(self.env["XDG_DATA_HOME"]) / "skl" / "index.json").unlink()
        r = self.cli("notes", "")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertEqual(self.cli("co").stdout, "completion\n")

    def test_no_words(self):
        r = self.run_cli("__complete", "--")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
