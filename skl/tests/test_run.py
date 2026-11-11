import unittest
from pathlib import Path

from helpers import SklCase, load_skl

skl = load_skl()


class RunTests(SklCase):
    def setUp(self):
        super().setUp()
        self.put_skill(self.tmp / "work" / ".claude" / "skills", "notes")
        r = self.run_cli("sync")
        self.assertEqual(r.returncode, 0, r.stderr)

    def log(self):
        p = Path(self.env["SKL_STUB_LOG"])
        return p.read_text().splitlines() if p.exists() else []

    def test_quote_and_build(self):
        self.assertEqual(skl.quote_arg("farro=rice"), "farro=rice")
        self.assertEqual(skl.quote_arg("My note"), '"My note"')
        self.assertEqual(skl.quote_arg('say "hi" \\ $x'), '"say \\"hi\\" \\\\ $x"')
        self.assertEqual(skl.quote_arg(""), '""')
        self.assertEqual(skl.build_command("notes", ["add", "My note", "--tag", "a b"]),
                         '/notes add "My note" --tag "a b"')

    def test_terminal_mode(self):
        self.make_stub("claude")
        r = self.run_cli("notes", "add", "My $HOME note", "--commit")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.log(), ['/notes add "My $HOME note" --commit', "--END--"])

    def test_tricky_args_intact(self):
        self.make_stub("claude")
        r = self.run_cli("notes", "add", 'say "hi" $x', "--tag=a b", "--tag", "-dash")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.log(),
                         ['/notes add "say \\"hi\\" $x" "--tag=a b" --tag -dash', "--END--"])

    def test_print_mode_and_exit_code(self):
        self.make_stub("claude", exit_code=3)
        r = self.run_cli("run", "notes", "list", "--print")
        self.assertEqual(r.returncode, 3)
        self.assertEqual(self.log(), ["-p", "/notes list", "--END--"])

    def test_app_mode(self):
        self.make_stub("xdg-open")
        self.make_stub("open")
        r = self.run_cli("notes", "add", "My note", "--app")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.log()[0], "https://claude.ai/new?q=%2Fnotes%20add%20%22My%20note%22")
        self.assertIn("opening https://claude.ai/new?q=", r.stderr)

    def test_app_mode_without_opener_prints_url(self):
        r = self.run_cli("notes", "list", "--app", env={**self.env, "PATH": str(Path(self.tmp) / "bin")})
        self.assertEqual(r.stdout.strip(), "https://claude.ai/new?q=%2Fnotes%20list")

    def test_help_and_validation_do_not_call_claude(self):
        self.make_stub("claude")
        r = self.run_cli("notes", "add", "--help")
        self.assertEqual(r.returncode, 0)
        self.assertTrue(r.stdout.startswith("/notes <action>"))
        r = self.run_cli("notes", "list", "--nope")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stderr.splitlines(),
                         ["error: unknown flag '--nope'", "usage: /notes <action> [<target>] [options]"])
        self.assertFalse(Path(self.env["SKL_STUB_LOG"]).exists())

    def test_missing_claude(self):
        r = self.run_cli("notes", "list")
        self.assertEqual(r.returncode, 127)
        self.assertIn("claude CLI not found", r.stderr)

    def test_unknown_skill(self):
        r = self.run_cli("nots", "list")
        self.assertEqual(r.returncode, 2)
        self.assertIn("error: unknown skill 'nots'", r.stderr)
        self.assertIn("did you mean: notes", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_split_mode_clash(self):
        e = {"interface": {"usage_line": "", "actions": {}, "groups": [{"label": "Global", "actions": None,
             "flags": [{"names": ["--print"], "takes_value": False, "choices": []}]}]}}
        self.assertEqual(skl.split_mode(e, ["go", "--print"]), ("terminal", ["go", "--print"]))
        self.assertEqual(skl.split_mode(e, ["go", "--skl-print"]), ("print", ["go"]))

    def test_both_modes(self):
        r = self.run_cli("notes", "list", "--print", "--app")
        self.assertEqual(r.returncode, 2)
        self.assertIn("choose one of --print and --app", r.stderr)

    def test_doctor(self):
        r = self.run_cli("doctor")
        self.assertEqual(r.returncode, 1)
        self.assertIn("claude: not found", r.stdout)
        self.make_stub("claude")
        r = self.run_cli("doctor")
        self.assertEqual(r.returncode, 0)
        self.assertIn("sign-in: ok", r.stdout)
        self.assertIn("skills: 1 indexed (0 pass-through)", r.stdout)


if __name__ == "__main__":
    unittest.main()
